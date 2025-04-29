#!/bin/bash
set -e

docker-compose down --remove-orphans

set -a
source .env
set +a

TSL_IDS=$(echo "$TSL_ID" | tr ',' ' ')
TSL_ID_CSV=$(echo "$TSL_ID" | tr ' ' ',')

# Download all files for each TSL ID using the agent service
for TSL in $TSL_IDS; do
  echo "Downloading files for $TSL ..."
  docker-compose run --rm \
    -e USER_ID="$USER_ID" \
    -e SUBSCRIBER="$SUBSCRIBER" \
    -e PASSWORD="$PASSWORD" \
    agent --user-id "$USER_ID" --subscriber "$SUBSCRIBER" --password "$PASSWORD" --tsl-id "$TSL"
done

# Copy PDFs from agent download directory to report/vrs/ so automate_regex can find them
mkdir -p report/vrs
for TSL in $TSL_IDS; do
  PDF_SRC=$(find get-vrs-report-pcaps/downloads/$TSL -type f -name '*.pdf' | head -n 1)
  if [ -n "$PDF_SRC" ]; then
    cp "$PDF_SRC" report/vrs/
  else
    echo "No PDF found for $TSL in agent download directory."
  fi
done

# Run automate_regex for all TSL IDs at once
PDF_DIR="report/vrs"
echo "Running automate_regex for TSL IDs: $TSL_ID_CSV"
docker-compose run --rm automate_regex python src/automate_regex.py --tsl_id "$TSL_ID_CSV" --pdf_dir "$PDF_DIR" --access_key "$AWS_ACCESS_KEY_ID" --secret_key "$AWS_SECRET_ACCESS_KEY"

# Run extract_filter for all TSL IDs at once (no explicit python call, entrypoint is set)
echo "Running extract_filter for TSL IDs: $TSL_ID_CSV"
docker-compose run --rm extract_filter --tsl_id "$TSL_ID_CSV"

# Run run_regex for all TSL IDs at once
echo "Running run_regex for TSL IDs: $TSL_ID_CSV"
docker-compose run --rm run_regex python src/run_regex_on_pcaps.py --tsl_id "$TSL_ID_CSV"

# Generate dashboard after all processing is complete
python3 src/generate_dashboard.py

echo "All services completed for TSL IDs: $TSL_ID_CSV"
docker-compose down --remove-orphans
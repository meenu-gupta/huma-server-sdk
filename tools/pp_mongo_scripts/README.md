### How to run

To get all signed up users:
> $ mongo --host mongodb+srv://ppmaintenanceuser:<password>@<url>/pp_eu_prod --quiet --eval 'var mode="printuserwithcohortidcsv"' exporter.js > signed_up_cohort_id_map_to_register_date.csv

To get users don't have ids:
> $ mongo --host mongodb+srv://ppmaintenanceuser:<password>@<url>/pp_eu_prod --quiet --eval 'var mode="printuserwithoutcohortidcsv"' exporter.js > signed_up_without_cohort_id.csv

To get fenland stats:
> $ mongo --host mongodb+srv://ppmaintenanceuser:<password>@<url>/pp_eu_prod --quiet --eval 'var mode="printstats"' exporter.js > stats.txt

To get afib sign up time:
> $ mongo --host mongodb+srv://ppmaintenanceuser:<password>@<url>/pp_us_prod --quiet --eval 'var mode="printuserscsv"' afib_deployment_stats.js > patient_ids_sign_up_time.csv

#### NOTE
Remove mongo cli logging from begging of files
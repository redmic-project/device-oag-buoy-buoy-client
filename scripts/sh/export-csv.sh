#!/bin/sh

currDate=$(date +%G-%m-%d)
currDay=$(date +%d)
currMonth=$(date +%m)
currYear=$(date +%G)

outputPath="${mountPath}/csv/${dbTable}/${currYear}/${currMonth}" 

mkdir -p "${outputPath}"

echo "\\\copy (select * from ${dbTable} where ${dbTable}.date >= date '${currDate}' - interval '24 hour' and ${dbTable}.date < date '${currDate}') to '${outputPath}/${dbTable}-${currDate}.csv' with csv header" | psql ${dbName}

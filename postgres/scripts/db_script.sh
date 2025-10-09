#!/bin/sh
export PGUSER="postgres"
psql -c "CREATE DATABASE djinventory"
psql djinventory -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

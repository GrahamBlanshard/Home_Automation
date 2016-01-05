#!/bin/bash

cat /dev/null > garage.db
sqlite3 garage.db "CREATE TABLE events (ID INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, name TEXT, etime TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"

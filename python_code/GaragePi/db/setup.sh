#!/bin/bash

cat /dev/null > garage.db
sqlite3 garage.db "CREATE TABLE events (ID INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, name TEXT, duration INTEGER, etime TIMESTAMP DEFAULT (datetime('now','localtime')));"

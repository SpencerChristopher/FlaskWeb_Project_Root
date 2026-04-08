#!/bin/sh
set -eu

APP_DB="${MONGO_APP_DB:-appdb}"
TEST_DB="${MONGO_TEST_DB:-pytest_appdb}"
APP_USER="${MONGO_APP_USER:?MONGO_APP_USER must be set}"
APP_PASSWORD="${MONGO_APP_PASSWORD:?MONGO_APP_PASSWORD must be set}"

if command -v mongosh >/dev/null 2>&1; then
  MONGO_SHELL="mongosh"
else
  MONGO_SHELL="mongo"
fi

"$MONGO_SHELL" --quiet \
  --username "$MONGO_INITDB_ROOT_USERNAME" \
  --password "$MONGO_INITDB_ROOT_PASSWORD" \
  --authenticationDatabase admin <<EOF
const appDbName = "${APP_DB}";
const testDbName = "${TEST_DB}";
const appUser = "${APP_USER}";
const appPassword = "${APP_PASSWORD}";

const appDb = db.getSiblingDB(appDbName);
const roles = [{ role: "readWrite", db: appDbName }];
if (testDbName && testDbName !== appDbName) {
  roles.push({ role: "readWrite", db: testDbName });
}

const existingUser = appDb.getUser(appUser);
if (!existingUser) {
  appDb.createUser({
    user: appUser,
    pwd: appPassword,
    roles: roles,
  });
  print("Created MongoDB application user '" + appUser + "' with roles on [" + appDbName + ", " + testDbName + "]");
} else {
  appDb.updateUser(appUser, {
    pwd: appPassword,
    roles: roles,
  });
  print("Updated MongoDB application user '" + appUser + "' roles/password");
}
EOF

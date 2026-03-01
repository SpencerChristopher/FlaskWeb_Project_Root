const appDbName = process.env.MONGO_APP_DB || "appdb";
const testDbName = process.env.MONGO_TEST_DB || "pytest_appdb";
const appUser = process.env.MONGO_APP_USER;
const appPassword = process.env.MONGO_APP_PASSWORD;

if (!appUser || !appPassword) {
  throw new Error("MONGO_APP_USER and MONGO_APP_PASSWORD must be set");
}

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
  print(`Created MongoDB application user '${appUser}' with roles on [${appDbName}, ${testDbName}]`);
} else {
  appDb.updateUser(appUser, {
    pwd: appPassword,
    roles: roles,
  });
  print(`Updated MongoDB application user '${appUser}' roles/password`);
}

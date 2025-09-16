db = db.getSiblingDB('appdb');

db.createUser({
  user: 'webserver',
  pwd: 'password',
  roles: [{ role: 'readWrite', db: 'appdb' }],
});

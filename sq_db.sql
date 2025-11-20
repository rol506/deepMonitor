CREATE TABLE IF NOT EXISTS company (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(255),
  fullName VARCHAR(255) NOT NULL,
  shortName VARCHAR(255) NOT NULL,
  TID VARCHAR(255) NOT NULL,
  accreditationDate DATE,
  leaderTID VARCHAR(255),
  leaderName VARCHAR(255),
  mainActivity VARCHAR(255),
  earnings INTEGER,
  expenses INTEGER,
  taxPayed INTEGER,
  workerCountMean INTEGER,
  vacansyCount INTEGER,
  isActive INTEGER,
  taxMode VARCHAR(255),
  taxDebt VARCHAR(255)
);

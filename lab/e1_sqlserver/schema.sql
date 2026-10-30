-- Disposable SQL Server E1c schema. Never apply to a customer database.
DROP TABLE IF EXISTS dbo.outbox;
DROP TABLE IF EXISTS dbo.postings;
DROP TABLE IF EXISTS dbo.operations;
DROP TABLE IF EXISTS dbo.duty;
DROP TABLE IF EXISTS dbo.accounts;

CREATE TABLE dbo.accounts (
    id INT NOT NULL PRIMARY KEY,
    balance BIGINT NOT NULL CHECK (balance >= 0)
);
CREATE TABLE dbo.operations (
    id NVARCHAR(80) NOT NULL PRIMARY KEY,
    src INT NOT NULL REFERENCES dbo.accounts(id),
    dst INT NOT NULL REFERENCES dbo.accounts(id),
    amount BIGINT NOT NULL CHECK (amount > 0),
    status NVARCHAR(24) NOT NULL CHECK (status IN (N'COMMITTED', N'REJECTED')),
    CONSTRAINT ck_operation_accounts CHECK (src <> dst)
);
CREATE TABLE dbo.postings (
    op NVARCHAR(80) NOT NULL REFERENCES dbo.operations(id),
    account INT NOT NULL REFERENCES dbo.accounts(id),
    delta BIGINT NOT NULL CHECK (delta <> 0),
    CONSTRAINT pk_postings PRIMARY KEY (op, account)
);
CREATE TABLE dbo.outbox (
    op NVARCHAR(80) NOT NULL PRIMARY KEY REFERENCES dbo.operations(id),
    event NVARCHAR(50) NOT NULL
);
CREATE TABLE dbo.duty (
    id INT NOT NULL PRIMARY KEY,
    active BIT NOT NULL
);
INSERT dbo.accounts(id,balance)
SELECT v.id, CONVERT(BIGINT,100000)
FROM (VALUES (1),(2),(3),(4),(5),(6),(7),(8),
             (9),(10),(11),(12),(13),(14),(15),(16)) v(id);
INSERT dbo.duty(id,active) VALUES (1,1),(2,1);

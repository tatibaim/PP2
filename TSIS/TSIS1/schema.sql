CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

INSERT INTO groups (name)
VALUES
    ('Family'),
    ('Work'),
    ('Friend'),
    ('Other')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100),
    birthday DATE,
    group_id INTEGER REFERENCES groups(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE contacts
    ADD COLUMN IF NOT EXISTS email VARCHAR(100),
    ADD COLUMN IF NOT EXISTS birthday DATE,
    ADD COLUMN IF NOT EXISTS group_id INTEGER REFERENCES groups(id),
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'contacts_name_key'
    ) AND NOT EXISTS (
        SELECT name
        FROM contacts
        GROUP BY name
        HAVING COUNT(*) > 1
    ) THEN
        ALTER TABLE contacts
        ADD CONSTRAINT contacts_name_key UNIQUE (name);
    END IF;
END $$;

UPDATE contacts
SET created_at = CURRENT_TIMESTAMP
WHERE created_at IS NULL;

UPDATE contacts
SET group_id = (
    SELECT id
    FROM groups
    WHERE name = 'Other'
)
WHERE group_id IS NULL;

CREATE TABLE IF NOT EXISTS phones (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('home', 'work', 'mobile')),
    CONSTRAINT phones_contact_phone_key UNIQUE (contact_id, phone)
);

INSERT INTO phones (contact_id, phone, type)
SELECT c.id, c.phone, 'mobile'
FROM contacts c
WHERE c.phone IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM phones p
      WHERE p.contact_id = c.id
        AND p.phone = c.phone
  );

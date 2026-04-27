CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone VARCHAR,
    p_type VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id INTEGER;
    v_matches INTEGER;
    v_phone_type VARCHAR(10);
BEGIN
    v_phone_type := LOWER(TRIM(p_type));

    IF v_phone_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Phone type must be home, work, or mobile.';
    END IF;

    SELECT COUNT(*), MIN(id)
    INTO v_matches, v_contact_id
    FROM contacts
    WHERE name = TRIM(p_contact_name);

    IF v_matches = 0 THEN
        RAISE EXCEPTION 'Contact % was not found.', p_contact_name;
    ELSIF v_matches > 1 THEN
        RAISE EXCEPTION 'More than one contact matches name %.', p_contact_name;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, TRIM(p_phone), v_phone_type)
    ON CONFLICT (contact_id, phone) DO UPDATE
    SET type = EXCLUDED.type;
END;
$$;

CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id INTEGER;
    v_matches INTEGER;
    v_group_name VARCHAR(50);
BEGIN
    v_group_name := INITCAP(TRIM(p_group_name));

    SELECT COUNT(*), MIN(id)
    INTO v_matches, v_contact_id
    FROM contacts
    WHERE name = TRIM(p_contact_name);

    IF v_matches = 0 THEN
        RAISE EXCEPTION 'Contact % was not found.', p_contact_name;
    ELSIF v_matches > 1 THEN
        RAISE EXCEPTION 'More than one contact matches name %.', p_contact_name;
    END IF;

    INSERT INTO groups (name)
    VALUES (v_group_name)
    ON CONFLICT (name) DO UPDATE
    SET name = EXCLUDED.name
    RETURNING id INTO v_group_id;

    UPDATE contacts
    SET group_id = v_group_id
    WHERE id = v_contact_id;
END;
$$;

CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    contact_id INTEGER,
    name VARCHAR,
    email VARCHAR,
    birthday DATE,
    group_name VARCHAR,
    phone VARCHAR,
    phone_type VARCHAR,
    created_at TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.email,
        c.birthday,
        COALESCE(g.name, 'Other') AS group_name,
        COALESCE(p.phone, c.phone),
        COALESCE(p.type, 'mobile'),
        c.created_at
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE c.name ILIKE '%' || p_query || '%'
       OR COALESCE(c.email, '') ILIKE '%' || p_query || '%'
       OR COALESCE(c.phone, '') ILIKE '%' || p_query || '%'
       OR COALESCE(p.phone, '') ILIKE '%' || p_query || '%'
    ORDER BY c.name, p.type, p.phone;
END;
$$;

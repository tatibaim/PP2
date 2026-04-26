-- 1. Процедура Upsert (обновить, если есть; вставить, если нет)
CREATE OR REPLACE PROCEDURE upsert_contact(p_name VARCHAR, p_phone VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM contacts WHERE name = p_name) THEN
        UPDATE contacts SET phone = p_phone WHERE name = p_name;
    ELSE
        INSERT INTO contacts(name, phone) VALUES(p_name, p_phone);
    END IF;
END;
$$;

-- 2. Процедура массовой вставки с валидацией (INOUT параметр для возврата ошибок)
CREATE OR REPLACE PROCEDURE bulk_insert_contacts(
    p_names VARCHAR[],
    p_phones VARCHAR[],
    INOUT invalid_data VARCHAR[] DEFAULT '{}'
)
LANGUAGE plpgsql AS $$
DECLARE
    i INT;
BEGIN
    invalid_data := '{}';
    FOR i IN 1 .. array_length(p_names, 1) LOOP
        -- Простая валидация: номер не пустой и содержит только цифры и плюс
        IF p_phones[i] ~ '^\+?[0-9]+$' THEN
            -- Вызываем наш же upsert для корректной вставки
            CALL upsert_contact(p_names[i], p_phones[i]);
        ELSE
            -- Если номер кривой, добавляем в массив неверных данных
            invalid_data := array_append(invalid_data, p_names[i] || ' (' || p_phones[i] || ')');
        END IF;
    END LOOP;
END;
$$;

-- 3. Процедура удаления по имени или телефону
CREATE OR REPLACE PROCEDURE delete_contact(p_search_val VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM contacts 
    WHERE name = p_search_val OR phone = p_search_val;
END;
$$;
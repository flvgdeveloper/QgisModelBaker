BEGIN;
SET search_path = {0}, pg_catalog;
CREATE OR REPLACE FUNCTION insert_update_delete_oid()
  RETURNS trigger AS
$BODY$
DECLARE
    column_name text;
BEGIN
  column_name := CASE
	WHEN TG_TABLE_NAME::text = 'persona'::text THEN 'persona_pid'::text
	WHEN TG_TABLE_NAME::text = 'predio'::text THEN 'predio_uid'::text
	WHEN TG_TABLE_NAME::text = 'derecho'::text THEN 'derecho_rid'::text
      END;

  IF (TG_OP = 'DELETE') THEN
    EXECUTE 'DELETE FROM {0}.oid WHERE ' || column_name || ' = ' || OLD.t_id;
  ELSIF (TG_OP = 'UPDATE' AND NEW.t_id <> OLD.t_id) THEN
    EXECUTE 'UPDATE {0}.oid set ' || column_name || ' = ' || NEW.t_id || ' WHERE ' || column_name || ' = ' || OLD.t_id;
  ELSIF (TG_OP = 'INSERT') THEN
    EXECUTE 'INSERT INTO {0}.oid (namespace,localid,' || column_name || ') VALUES (' || quote_literal('catastro') || ',' || quote_literal(TG_TABLE_NAME || '_' || NEW.t_id ) || ',' || NEW.t_id || ' );';
  END IF;
  return null;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;




ALTER TABLE predio_tipo ADD CONSTRAINT predio_tipo_ilicode_key UNIQUE (ilicode);
ALTER TABLE predio
  ADD FOREIGN KEY (atype) REFERENCES predio_tipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE persona_tipo ADD CONSTRAINT persona_tipo_ilicode_key UNIQUE (ilicode);
ALTER TABLE persona
  ADD FOREIGN KEY (atype) REFERENCES persona_tipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE persona_tipodocumento ADD CONSTRAINT persona_tipodocumento_ilicode_key UNIQUE (ilicode);
ALTER TABLE persona
  ADD FOREIGN KEY (tipodocumento) REFERENCES persona_tipodocumento (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE derecho_tipo ADD CONSTRAINT derecho_tipo_ilicode_key UNIQUE (ilicode);
ALTER TABLE derecho
  ADD FOREIGN KEY (atype) REFERENCES derecho_tipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;


CREATE TRIGGER trigger_predio_insert_oid  AFTER INSERT
  ON predio
  FOR EACH ROW EXECUTE PROCEDURE insert_update_delete_oid();

CREATE TRIGGER trigger_persona_insert_oid  AFTER INSERT
  ON persona
  FOR EACH ROW EXECUTE PROCEDURE insert_update_delete_oid();

CREATE TRIGGER trigger_derecho_insert_oid  AFTER INSERT
  ON derecho
  FOR EACH ROW EXECUTE PROCEDURE insert_update_delete_oid();


SET search_path = public, pg_catalog;

COMMIT;


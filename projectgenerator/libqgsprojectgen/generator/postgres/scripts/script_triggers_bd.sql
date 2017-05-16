BEGIN;
SET search_path = {0}, pg_catalog;


CREATE OR REPLACE FUNCTION {0}.insert_update_delete_oid()
  RETURNS trigger AS
$BODY$
DECLARE
    column_name text;
BEGIN
  column_name := CASE
	      WHEN TG_TABLE_NAME::text = 'zonaot'::text THEN 'zonaot_uid'::text
	      WHEN TG_TABLE_NAME::text = 'responsabilidadot'::text THEN 'responsabilidadot_rid'::text
	      WHEN TG_TABLE_NAME::text = 'responsableot'::text THEN 'responsableot_pid'::text
	      WHEN TG_TABLE_NAME::text = 'restriccionot'::text THEN 'restriccionot_rid'::text
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


CREATE TRIGGER insert_update_delete_oid AFTER INSERT
  ON {0}.zonaot
  FOR EACH ROW EXECUTE PROCEDURE {0}.insert_update_delete_oid();

CREATE TRIGGER insert_update_delete_oid  AFTER INSERT
  ON {0}.responsabilidadot
  FOR EACH ROW EXECUTE PROCEDURE {0}.insert_update_delete_oid();

CREATE TRIGGER insert_update_delete_oid  AFTER INSERT
  ON {0}.responsableot
  FOR EACH ROW EXECUTE PROCEDURE {0}.insert_update_delete_oid();

CREATE TRIGGER insert_update_delete_oid  AFTER INSERT
  ON {0}.restriccionot
  FOR EACH ROW EXECUTE PROCEDURE {0}.insert_update_delete_oid();




ALTER TABLE estructuratipo ADD CONSTRAINT estructura_tipo_ilicode_key UNIQUE (ilicode);
ALTER TABLE zonaot
  ADD FOREIGN KEY (estructura) REFERENCES estructuratipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE protecciontipo ADD CONSTRAINT proteccion_tipo_ilicode_key UNIQUE (ilicode);
ALTER TABLE zonaot
  ADD FOREIGN KEY (sueloproteccion) REFERENCES protecciontipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE responsabletipo ADD CONSTRAINT responsable_tipo_ilicode_key UNIQUE (ilicode);
ALTER TABLE responsableot
  ADD FOREIGN KEY (atype) REFERENCES responsabletipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE restriccionottipo ADD CONSTRAINT tipo_restriccion_ot_ilicode_key UNIQUE (ilicode);
ALTER TABLE restriccionot
  ADD FOREIGN KEY (atype) REFERENCES restriccionottipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE responsabilidadtipo ADD CONSTRAINT tipo_responsabilidad_ot_ilicode_key UNIQUE (ilicode);
ALTER TABLE responsabilidadot
  ADD FOREIGN KEY (atype) REFERENCES responsabilidadtipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE subestructuratipo ADD CONSTRAINT subestructura_tipo_ilicode_key UNIQUE (ilicode);
ALTER TABLE zonaot
  ADD FOREIGN KEY (subestructura) REFERENCES subestructuratipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE suelotipo ADD CONSTRAINT suelo_tipo_ilicode_key UNIQUE (ilicode);
ALTER TABLE zonaot
  ADD FOREIGN KEY (suelo) REFERENCES suelotipo (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE la_baunittype ADD CONSTRAINT la_baunittype_ilicode_key UNIQUE (ilicode);
ALTER TABLE zonaot
  ADD FOREIGN KEY (atype) REFERENCES la_baunittype (ilicode) ON UPDATE NO ACTION ON DELETE NO ACTION;





SET search_path = public, pg_catalog;

COMMIT;


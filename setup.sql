DROP TABLE IF EXISTS acmplus;

CREATE TABLE acmplus (
    id BIGSERIAL PRIMARY KEY,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    vx double precision,
    vy double precision,
    speed double precision,
    direction double precision,
    water_temp double precision,
    sended BOOLEAN default false,
    num_attempts SMALLINT default 0
);

DROP TABLE IF EXISTS pb200;

CREATE TABLE pb200 (
    id BIGSERIAL PRIMARY KEY,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    press_inch double precision,
    press_mbar double precision,
    air_temp double precision,
    water_temp double precision,
    rel_humidity double precision,
    abs_humidity double precision,
    dew_point double precision,
    wind_dir_true double precision,
    wind_dir_magnetic double precision,
    wind_knots double precision,
    wind_meters double precision,
    sended BOOLEAN default false,
    num_attempts SMALLINT default 0
);

CREATE OR REPLACE FUNCTION increment_num_attempts()
    RETURNS trigger AS
$BODY$
	BEGIN
		NEW.num_attempts := OLD.num_attempts + 1;
		RETURN NEW;
	END;
$BODY$
  LANGUAGE plpgsql;

CREATE TRIGGER pb200_increment_num_attemps_before_update
	BEFORE UPDATE
	ON pb200
	FOR EACH ROW
	EXECUTE PROCEDURE increment_num_attempts();

CREATE TRIGGER acmplus_increment_num_attemps_before_update
	BEFORE UPDATE
	ON acmplus
	FOR EACH ROW
	EXECUTE PROCEDURE increment_num_attempts();
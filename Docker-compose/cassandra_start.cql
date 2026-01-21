-- Create a keyspace
CREATE KEYSPACE IF NOT EXISTS forecast_test WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : '1' };

CREATE TABLE forecast_test.forecast (
	id text,
	register_type text,
	datetime timestamp,
	request timestamp,
	algorithm text,
	horizon text,
	last_updated timestamp,
	model_info text,
	q05 float,
	q10 float,
	q20 float,
	q30 float,
	q40 float,
	q50 float,
	q60 float,
	q70 float,
	q80 float,
	q90 float,
	q95 float,
	units text,
	PRIMARY KEY (( id, register_type ), datetime, request)
) WITH CLUSTERING ORDER BY ( datetime DESC, request DESC );


CREATE TABLE forecast_test.installations (
	id text,
	country text,
	generation int,
	id_type text,
    installed_capacity float,
	is_active int,
	last_updated timestamp,
	latitude float,
	latitude_nwp float,
	longitude float,
	longitude_nwp float,
	net_power_types text,
	source_nwp text,
	PRIMARY KEY (id)
);


CREATE TABLE forecast_test.metrics_2wk (
	id text,
	register_type text,
	request timestamp,
	horizon text,
	crps float,
	last_updated timestamp,
	mae float,
	nmae float,
	nrmse float,
	rmse float,
	PRIMARY KEY (( id, register_type ), request, horizon)
) WITH CLUSTERING ORDER BY ( request DESC, horizon ASC );



CREATE TABLE forecast_test.metrics_year (
	id text,
	register_type text,
	request timestamp,
	horizon text,
	crps float,
	last_updated timestamp,
	mae float,
	nmae float,
	nrmse float,
	rmse float,
	PRIMARY KEY (( id, register_type ), request, horizon)
) WITH CLUSTERING ORDER BY ( request DESC, horizon ASC );


CREATE TABLE forecast_test.models_info (
	id text,
	last_train timestamp,
	last_updated timestamp,
	model_in_use FROZEN<MAP<text, FROZEN<MAP<text, text>>>>,
	model_ref FROZEN<MAP<text, FROZEN<MAP<text, text>>>>,
	to_train int,
	PRIMARY KEY (id)
);


CREATE TABLE forecast_test.raw (
	id text,
	register_type text,
	datetime timestamp,
	last_updated timestamp,
	units text,
	value float,
	PRIMARY KEY (( id, register_type ), datetime)
) WITH CLUSTERING ORDER BY ( datetime DESC );

CREATE TABLE forecast_test.net (
	id text,
	register_type text,
	datetime timestamp,
	last_updated timestamp,
	units text,
	value float,
	PRIMARY KEY (( id, register_type ), datetime)
) WITH CLUSTERING ORDER BY ( datetime DESC );


CREATE TABLE forecast_test.processed (
	id text,
	register_type text,
	datetime timestamp,
	estimated float,
	last_updated timestamp,
	units text,
	value float,
	PRIMARY KEY (( id, register_type ), datetime)
) WITH CLUSTERING ORDER BY ( datetime DESC );


CREATE TABLE forecast_test.nwp_grid (
	source text,
	latitude float,
	longitude float,
	is_active int,
	last_request timestamp,
    last_updated timestamp,
	inserted_at timestamp,
	variables text,
	PRIMARY KEY (source, latitude, longitude)
);


CREATE TABLE forecast_test.nwp_solar (
	source text,
	latitude float,
	longitude float,
	datetime timestamp,
	request timestamp,
	cfh float,
	cfl float,
	cfm float,
	cft float,
	last_updated timestamp,
	swflx float,
	temp float,
	PRIMARY KEY (( source, latitude, longitude ), datetime, request)
) WITH CLUSTERING ORDER BY ( datetime DESC, request DESC );


CREATE TABLE forecast_test.nwp_wind (
	source text,
	latitude float,
	longitude float,
	datetime timestamp,
	request timestamp,
	dir float,
	last_updated timestamp,
	mod float,
	u float,
	ulev1 float,
	ulev2 float,
	ulev3 float,
	v float,
	vlev1 float,
	vlev2 float,
	vlev3 float,
	PRIMARY KEY (( source, latitude, longitude ), datetime, request)
) WITH CLUSTERING ORDER BY ( datetime DESC, request DESC );


CREATE TABLE forecast_test.users_rest (
	username text,
	last_login timestamp,
	password_hash text,
	permissions text,
	registered_at timestamp,
	userinfo text,
	PRIMARY KEY (username)
);


CREATE TABLE forecast_test.objects
(
    id          text,
    model_id    text,
    obj_id      text,
    last_update timestamp,
    obj_serial  text,
    PRIMARY KEY (id, model_id, obj_id)
);

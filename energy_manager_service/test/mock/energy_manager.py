import psycopg2
from datetime import datetime, timedelta

from energy_manager_service.test.config import Config

from energy_manager_service.models.database.energy_manager_db import DBAvailableFlexbility, DBOptimizedCycles
from energy_manager_service import db

dt_plus_23_hours = datetime.now() + timedelta(hours=23)
dt_plus_6_hours = datetime.now() + timedelta(hours=6)
dt_plus_10_hours = datetime.now() + timedelta(hours=10)


def mock_energy_manager():
    conn = psycopg2.connect(
        f"dbname={Config.DATABASE_NAME} user={Config.DATABASE_USER} password={Config.DATABASE_PASSWORD} host={Config.DATABASE_IP}")
    cur = conn.cursor()

    cur.execute(
        f"INSERT INTO flexibility_available (flex_id, user_id, meter_id, request_datetime, accepted_by_grid, baseline_call_ok, flex_up_call_ok, flex_down_call_ok, baseline_zeros, flex_up_zeros) VALUES (1, '1234567890', 'meter_id_example', '{datetime.now().isoformat()}', True, True, True, True, True, True)")
    # Cycle was not canceled before activation
    cur.execute(
        f"INSERT INTO optimized_cycles (sequence_id, serial_number, current_start_time, optimized_start_time, optimized_end_time, auto_management, flex_type, accepted_by_user, notification_sent, delay_call_ok, delay_call_description, cycle_cancelled_before_activation, flex_id) VALUES (1, 'serial_number_example', '{dt_plus_23_hours.isoformat()}', '{dt_plus_6_hours.isoformat()}', '{dt_plus_10_hours.isoformat()}', True, 'baseline', True, False, True, '', False, 1)")
    cur.execute(
        f"INSERT INTO optimized_cycles (sequence_id, serial_number, current_start_time, optimized_start_time, optimized_end_time, auto_management, flex_type, accepted_by_user, notification_sent, delay_call_ok, delay_call_description, cycle_cancelled_before_activation, flex_id) VALUES (1, 'serial_number_example', '{dt_plus_23_hours.isoformat()}', '{dt_plus_6_hours.isoformat()}', '{dt_plus_10_hours.isoformat()}', True, 'up', True, False, True, '', False, 1)")
    # Cycle was canceled before activation
    cur.execute(
        f"INSERT INTO optimized_cycles (sequence_id, serial_number, current_start_time, optimized_start_time, optimized_end_time, auto_management, flex_type, accepted_by_user, notification_sent, delay_call_ok, delay_call_description, cycle_cancelled_before_activation, flex_id) VALUES (2, 'serial_number_example', '{dt_plus_23_hours.isoformat()}', '{dt_plus_6_hours.isoformat()}', '{dt_plus_10_hours.isoformat()}', True, 'baseline', True, False, True, '', True, 1)")
    cur.execute(
        f"INSERT INTO optimized_cycles (sequence_id, serial_number, current_start_time, optimized_start_time, optimized_end_time, auto_management, flex_type, accepted_by_user, notification_sent, delay_call_ok, delay_call_description, cycle_cancelled_before_activation, flex_id) VALUES (2, 'serial_number_example', '{dt_plus_23_hours.isoformat()}', '{dt_plus_6_hours.isoformat()}', '{dt_plus_10_hours.isoformat()}', True, 'up', True, False, True, '', True, 1)")

    conn.commit()

    cur.close()
    conn.close()


def mock_energy_manager2(user_id="1234567890"):
    flex = create_available_flex(user_id, 'meter_id_example', datetime.now(),
                                 True, True, True, True, True, True)

    create_optimized_cicles(flex.flex_id, 1, "serial_number_example", dt_plus_23_hours,
                            dt_plus_6_hours, dt_plus_10_hours, True, 'baseline', True, False, True, '', False)
    create_optimized_cicles(flex.flex_id, 1, "serial_number_example", dt_plus_23_hours,
                            dt_plus_6_hours, dt_plus_10_hours, True, 'up', True, False, True, '', False)
    create_optimized_cicles(flex.flex_id, 2, "serial_number_example", dt_plus_23_hours,
                            dt_plus_6_hours, dt_plus_10_hours, True, 'baseline', True, False, True, '', True)
    create_optimized_cicles(flex.flex_id, 2, "serial_number_example", dt_plus_23_hours,
                            dt_plus_6_hours, dt_plus_10_hours, True, 'up', True, False, True, '', True)


def create_optimized_cicles(
    flex_id, sequence_id, serial_number, current_start_time, optimized_start_time,
    optimized_end_time, auto_management=True, flex_type='baseline', accepted_by_user=False,
    notification_sent=False, delay_call_ok=True, delay_call_description="desc", cycle_cancelled_before_activation=False
):
    cycle = DBOptimizedCycles(flex_id=flex_id,
                              sequence_id=sequence_id,
                              serial_number=serial_number,
                              current_start_time=current_start_time,
                              optimized_start_time=optimized_start_time,
                              optimized_end_time=optimized_end_time,
                              auto_management=auto_management,
                              flex_type=flex_type,
                              accepted_by_user=accepted_by_user,
                              notification_sent=notification_sent,
                              delay_call_ok=delay_call_ok,
                              delay_call_description=delay_call_description,
                              cycle_cancelled_before_activation=cycle_cancelled_before_activation)
    db.session.add(cycle)
    db.session.commit()

    return cycle


def create_available_flex(
        user_id, meter_id, request_datetime, accepted_by_grid=True,
        baseline_call_ok=False, flex_up_call_ok=False, flex_down_call_ok=False,
        baseline_zeros=True, flex_up_zeros=True
):
    avai_flex = DBAvailableFlexbility(
        user_id=user_id,
        meter_id=meter_id,
        request_datetime=request_datetime,
        accepted_by_grid=accepted_by_grid,
        baseline_call_ok=baseline_call_ok,
        flex_up_call_ok=flex_up_call_ok,
        flex_down_call_ok=flex_down_call_ok,
        baseline_zeros=baseline_zeros,
        flex_up_zeros=flex_up_zeros)
    db.session.add(avai_flex)
    db.session.commit()

    return avai_flex


def mock_flexibility_available(flex_id, user_id, meter_id, accepted_by_grid=True):
    conn = psycopg2.connect(
        f"dbname={Config.DATABASE_NAME} user={Config.DATABASE_USER} password={Config.DATABASE_PASSWORD} host={Config.DATABASE_IP}")
    cur = conn.cursor()

    cur.execute(
        f"INSERT INTO flexibility_available (flex_id, user_id, meter_id, request_datetime, accepted_by_grid, baseline_call_ok, flex_up_call_ok, flex_down_call_ok, baseline_zeros, flex_up_zeros) "
        f"VALUES ({str(flex_id)}, '{user_id}', '{meter_id}', '{datetime.now().isoformat()}', {accepted_by_grid}, True, True, True, True, True)"
    )

    conn.commit()

    cur.close()
    conn.close()


def mock_optimized_cycle(sequence_id, serial_number, accepted_by_user, cycle_cancelled_before_activation, flex_id, optimized_start_time=None, optimized_end_time=None):
    if optimized_start_time is None:
        optimized_start_time = dt_plus_6_hours.isoformat()
    if optimized_end_time is None:
        optimized_end_time = dt_plus_10_hours.isoformat()

    conn = psycopg2.connect(
        f"dbname={Config.DATABASE_NAME} user={Config.DATABASE_USER} password={Config.DATABASE_PASSWORD} host={Config.DATABASE_IP}")
    cur = conn.cursor()

    cur.execute(
        f"INSERT INTO optimized_cycles (sequence_id, serial_number, current_start_time, optimized_start_time, optimized_end_time, auto_management, flex_type, accepted_by_user, notification_sent, delay_call_ok, delay_call_description, cycle_cancelled_before_activation, flex_id) "
        f"VALUES ({str(sequence_id)}, '{serial_number}', '{dt_plus_23_hours.isoformat()}', '{optimized_start_time}', '{optimized_end_time}', True, 'baseline', {accepted_by_user}, False, True, '', {cycle_cancelled_before_activation}, {str(flex_id)})"
    )
    # NOTE: To ease the tests in distinguishing up and baseline optimizations, notification_sent is set to False on 'baseline' and True on 'up'
    cur.execute(
        f"INSERT INTO optimized_cycles (sequence_id, serial_number, current_start_time, optimized_start_time, optimized_end_time, auto_management, flex_type, accepted_by_user, notification_sent, delay_call_ok, delay_call_description, cycle_cancelled_before_activation, flex_id) "
        f"VALUES ({str(sequence_id)}, '{serial_number}', '{dt_plus_23_hours.isoformat()}', '{optimized_start_time}', '{optimized_end_time}', True, 'up', {accepted_by_user}, True, True, '', {cycle_cancelled_before_activation}, {str(flex_id)})"
    )

    conn.commit()

    cur.close()
    conn.close()


def clear_energy_manager():
    conn = psycopg2.connect(
        f"dbname={Config.DATABASE_NAME} user={Config.DATABASE_USER} password={Config.DATABASE_PASSWORD} host={Config.DATABASE_IP}")
    cur = conn.cursor()

    cur.execute("DELETE FROM flexibility_available CASCADE")

    conn.commit()

    cur.close()
    conn.close()


def query_recommendation_by_id(rec_id):
    conn = psycopg2.connect(
        f"dbname={Config.DATABASE_NAME} user={Config.DATABASE_USER} password={Config.DATABASE_PASSWORD} host={Config.DATABASE_IP}")
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM optimized_cycles WHERE id = {rec_id}")
    result = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    return result


def query_recommendation(**kwargs):
    """
    Agnostic query function for the optimized_cycles table

    Example:
        - query_recommendation(flex_type='baseline', accepted_by_user=True)
            - Uses the query: SELECT * FROM optimized_cycles WHERE flex_type = 'baseline' AND accepted_by_user = True
    """
    conn = psycopg2.connect(
        f"dbname={Config.DATABASE_NAME} user={Config.DATABASE_USER} password={Config.DATABASE_PASSWORD} host={Config.DATABASE_IP}")
    cur = conn.cursor()

    where_clause = " AND ".join([f"{k} = '{v}'" if isinstance(
        v, str) else f"{k} = {v}" for k, v in kwargs.items()])
    cur.execute(f"SELECT * FROM optimized_cycles WHERE {where_clause}")
    result = cur.fetchall()
    print(result)

    conn.commit()

    cur.close()
    conn.close()

    return result


def query_recommendation_by_sequence_id_and_serial_number(sequence_id, serial_number):
    recommendations = DBOptimizedCycles.query.filter_by(
        sequence_id=sequence_id,
        serial_number=serial_number
    ).all()

    return recommendations

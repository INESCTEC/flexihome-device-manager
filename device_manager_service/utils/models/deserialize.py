from device_manager_service.models import MachineCycle, PowerProfile


def deserialize_washing_cycle(machine):
    cycles = []
    for cycle in machine.washing_cycles:
        power_profile = []
        for slot in cycle.power_profile:
            power_profile.append(
                PowerProfile(
                    slot=slot.slot,
                    max_power=slot.max_power,
                    min_power=slot.min_power,
                    expected_power=slot.expected_power,
                    power_units=slot.power_units,
                    duration=slot.duration,
                    duration_units=slot.duration_units,
                )
            )

        # TODO: Convert times to local time (they are stored in DB as UTC)
        cycles.append(
            MachineCycle(
                sequence_id=cycle.sequence_id,
                earliest_start_time=cycle.earliest_start_time,
                latest_end_time=cycle.latest_end_time,
                scheduled_start_time=cycle.scheduled_start_time,
                expected_end_time=cycle.expected_end_time,
                program=cycle.program,
                is_optimized=cycle.is_optimized,
                power_profile=power_profile,
            )
        )

    return cycles
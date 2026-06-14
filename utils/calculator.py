def calculate_parasitemia(
        parasite_count,
        rbc_count
):

    if rbc_count == 0:
        return 0

    parasitemia = (
        parasite_count / rbc_count
    ) * 100

    return round(parasitemia, 2)
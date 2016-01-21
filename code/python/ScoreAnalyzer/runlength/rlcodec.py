import numpy as np
from collections import Counter

def run_length_coding(array_data=np.array([])):
    if sum(array_data.shape) > 0:
        # Figure out all switched indices where the value of each index is different from the next value
        # i.e. find all i where arr[i] != arr[i+1]
        switch_pts = [i for i, x in enumerate(map(lambda x, y: x != y, array_data[:-1], array_data[1:])) if x]

        # Insert values such that the difference of switched indices is equal to run-length sequence
        switch_pts.insert(0, -1)
        switch_pts.append(len(array_data)-1)

        # Get run-length sequence
        run_length_sequence = np.diff(switch_pts)

        # Find out the corresponded set of each run-length
        sequence_id = (np.arange(len(run_length_sequence)) + array_data[0]) % 2

        # Each element consists of two values: (SET, RUN_LENGTH)
        return zip(sequence_id, run_length_sequence)
    else:
        return None

def run_length_distribution(data):
    # Aggregate RLC pairs
    hist = Counter(data)

    # Wrap unique elements and its corresponded count
    # ((SET_ID, RUN_LENGTH), COUNT)
    hist = zip(hist.keys(), hist.values())

    # Splitting by sets (0/1)
    # hist[0/1]: array of (RUN_LENGTH, COUNT) of the set 0/1
    hist = map(lambda v: filter(lambda x: x[0][0] == v, hist), [0, 1])
    hist = map(lambda v: map(lambda x: (x[0][1], x[1]), hist[v]), [0, 1])

    # Sort by count in descending order
    hist = map(lambda v: sorted(hist[v], key=lambda x: x[1], reverse=True), [0, 1])

    return hist
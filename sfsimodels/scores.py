import numpy as np


def lc_score(value):
    """
    Evaluates the accuracy of a predictive measure (e.g. r-squared)

    :param value: float, between 0.0 and 1.0.
    :return:
    """
    rebased = 2 * (value - 0.5)

    if rebased == 0:
        return 0
    elif rebased > 0:
        compliment = 1.0 - rebased
        score = - np.log2(compliment)
    else:
        compliment = 1.0 + rebased
        score = np.log2(compliment)
    return score


# def show_scores():
#     print(lc_score(0.2))
#
#     r_vals = 1.0 - np.logspace(-4, -0.01)
#     scores = []
#     print(r_vals)
#     for r in r_vals:
#         scores.append(lc_score(r))
#
#     plt.plot(r_vals, scores)
#     plt.show()
#
# if __name__ == '__main__':
#     show_scores()

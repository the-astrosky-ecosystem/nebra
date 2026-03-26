from time import time


if __name__ == "__main__":
    from .jetstream import event_stream

    # event_stream(collections=["eco.astrosky.transient.*"])
    one_day_ago = int((time() - 24 * 60**2) * 1e6)
    # one_day_ago = 1000000
    # event_stream(cursor=one_day_ago, handles=["emily.space"])
    event_stream(cursor=None, handles=["emily.space"])

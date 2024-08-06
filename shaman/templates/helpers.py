from datetime import datetime, timedelta, timezone


def last_seen(date_object):
    now = datetime.now(timezone.utc)
    difference = now - date_object
    formatted = ReadableSeconds(difference.seconds, days=difference.days)
    return "%s ago" % formatted


class ReadableSeconds(object):

    def __init__(self, seconds, days=None):
        self.original_seconds = seconds
        self.original_days = days

    @property
    def relative(self):
        """
        Generate a relative datetime object based on current seconds
        """
        return datetime(1, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=self.original_seconds)

    def __str__(self):
        return "{0}{1}{2}{3}{4}{5}".format(
            self.years,
            self.months,
            self.days,
            self.hours,
            self.minutes,
            self.seconds,
        ).rstrip(' ,')

    @property
    def years(self):
        # Subtract 1 here because the earliest datetime() is 1/1/1
        years = self.relative.year - 1
        year_str = 'years' if years > 1 else 'year'
        if years:
            return "%d %s, " % (years, year_str)
        return ""

    @property
    def months(self):
        # Subtract 1 here because the earliest datetime() is 1/1/1
        months = self.relative.month - 1
        month_str = 'months' if months > 1 else 'month'
        if months:
            return "%d %s, " % (months, month_str)
        return ""

    @property
    def days(self):
        days = self.original_days
        day_str = 'days' if days > 1 else 'day'
        if days:
            return "%d %s, " % (days, day_str)
        return ""

    @property
    def hours(self):
        hours = self.relative.hour
        hour_str = 'hours' if hours > 1 else 'hour'
        if hours:
            return "%d %s, " % (self.relative.hour, hour_str)
        return ""

    @property
    def minutes(self):
        minutes = self.relative.minute
        minutes_str = 'minutes' if minutes > 1 else 'minute'
        if minutes:
            return "%d %s, " % (self.relative.minute, minutes_str)
        return ""

    @property
    def seconds(self):
        seconds = self.relative.second
        seconds_str = 'seconds' if seconds > 1 else 'second'
        if seconds:
            return "%d %s, " % (self.relative.second, seconds_str)
        return ""


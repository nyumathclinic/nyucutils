import argparse
import click
import csv
import datetime
import logging
from lxml import etree
import lxml.html
import re
import sys

class WebassignMent(object):
    """Class to hold information about a WebAssign assignment

    Note on naming conventions: The company is called WebAssign.
    A natural name for an assignment published through WebAssign is a
    portmanteau _WebAssign-ment_ or _WebAssignment_.
    PEP 8 recommends StudlyCaps for class names, where each word in the name
    is simply capitalized.  Hence `XmlWriter` instead of `XMLWriter`.
    So rather than `WebAssignment`, which could be confused with a generic
    "web assignment", we go with `WebassignMent`.

    """
    def __init__(self,name=None,category=None,available=None,due=None):
        self.name=name
        self.category=category
        self.available=available
        self.due=due

def wadatetime_to_datetime(date_string):
    """convert a WebAssign date string to a `datetime.datetime` object
    """
    # TODO: replace debugging statements with doctests
    log = logging.getLogger("wadatetime_to_datetime")
    match = re.search(r'(\d+)-(\d+)-(\d+).(\d{2}):(\d{2}) (AM|PM).([A-Z]+)',date_string)
    log.debug('match: %s',match.groups())
    (month,day,year,hour,minute,ampm,time_zone) = match.groups()
    log.debug("month: %s",month)
    log.debug("day: %s",day)
    log.debug("year: %s",year)
    log.debug("hour: %s",hour)
    log.debug("minute: %s",minute)
    log.debug("ampm: %s",ampm)
    # Instantiate the datetime object.
    # This is a "naive" object; which is probably OK.
    dt = datetime.datetime(
        int(year)+2000,int(month),int(day),
        (int(hour) % 12) + (12 if ampm == 'PM' else 0),
        int(minute))
    log.debug("dt: %s",dt)
    return dt

def isodate_format(date):
    """Serialize a datetime.DateTime object with `ISO 8601`_ date style

    .. _`ISO 8601`: LINK
    """
    return date.strftime("%Y-%m-%d")

def localdatetime_format(date):
    """
    Serialize a datetime.DateTime object with local date/time style
    """
    # TODO: use the true local format from installation
    # Un-zero-pad hours and monthday
    return date.strftime("%A %B %d %I:%M%p").replace(" 0"," ")

def assignments_from_html(file):
    """
    Extract the assignment data from a WebAssign ClassView HTML page.

    return a list of WebassignMent objects
    """
    log = logging.getLogger('assignments_from_html')
    tree = lxml.html.parse(file)
    try:
        table=tree.xpath('//*[@id="wa"]/table/tbody/tr[3]/td[2]/div[2]/table/tbody')[0]
    except:
        raise
    assignments=[]
    for row in table:
        if (len(row) < 4):
            continue
        name=row[0].xpath('.//font/b/text()')[0]
        log.debug('name: %s',name)
        dates=row[3].xpath('font')[0]
        avail_date_string=dates.text
        log.debug("avail_date_string: %s", repr(avail_date_string)) # looks like [ 5-2-16 05:00 PM EDT ]
        due_date_string=dates[0].tail
        log.debug("due_date_string: %s", repr(due_date_string)) # looks like [ 5-2-16 05:00 PM EDT ]
        avail_date=wadatetime_to_datetime(avail_date_string)
        due_date=wadatetime_to_datetime(due_date_string)
        assignments.append(WebassignMent(name=name,available=avail_date,due=due_date))
    return assignments

@click.command()
@click.argument('input',type=click.Path(exists=True),metavar='FILE')
@click.option('-o','--output',
    type=click.File('w'),
    default='-',
    help='write to this file'
)
@click.option('-d','--debug',is_flag=True,default=False,help='print lots of debugging statments')
@click.option('-v','--verbose',is_flag=True,default=False,help="Be verbose")
def assignments_from_html_to_csv(input,output,debug,verbose):
    """Extract assignments from HTML page and export CSV
    """
    logging.basicConfig(level=(logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)))
    assignments = assignments_from_html(input)
    writer = csv.writer(output)
    writer.writerow(["startDate","endDate","announcementText"])
    for assignment in assignments:
        writer.writerow([isodate_format(assignment.available),
            isodate_format(assignment.due),
            "WebAssignment “%s” due %s" % (assignment.name,localdatetime_format(assignment.due))])

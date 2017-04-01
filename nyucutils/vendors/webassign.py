"""Classes and methods to interact with WebAssign

None of this is up-to-date with the interfaces designed in usage.txt.


"""
import argparse
import csv
import datetime
from datetime import datetime, date
import logging
import re
import sys

import pandas
import numpy
import click
from lxml import etree
import lxml.html

class WebassignMent(object):
    """Class to hold information about a WebAssign assignment

    Note on naming conventions: The company is called WebAssign.
    A natural name for an assignment published through WebAssign is a
    portmanteau *WebAssign-ment* or *WebAssignment*.
    PEP 8 recommends StudlyCaps for class names, where each word in the name
    is simply capitalized.  Hence :code:`XmlWriter` instead of :code:`XMLWriter`.
    So rather than :code:`WebAssignment`, which could be confused with a generic
    "web assignment", we go with :code:`WebassignMent`.

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


# not sure this is necessary.
class WagbParser(object):
    """Parses WebAssign GradeBook (sic) CSV (sic) files.
    Creates a WebAssignGradeBook"""

    def __init__(self,file=None):
        if file:
            self.file=file

    def parse(self):
        result=WebAssignGradeBook();

        # GradeBook metadata
        mddf=pandas.read_csv(self.file,nrows=3,sep='\t',header=None).T
        mddf.columns=['Section Name','Instructor','Date']
        metadata=mddf.loc[0]
        result.section_name=metadata['Section Name']
        result.instructor_name=metadata['Instructor']
        result.date=datetime.strptime(metadata['Date'],'%A, %B %d, %Y %I:%M %p %Z')

        # Category names
        categories=pandas.read_csv(self.file,sep='\t',skiprows=4,nrows=2,header=None,index_col=0).T.dropna()
        # warning: The regexp below assumes there are no spaces in the category name
        newcols=categories['Assignment Category'].str.extract('(?P<cat_name>[^ ]*)( \[(?P<cat_count>\d+)\])?',expand=True)
        del newcols[1]
        categories=categories.combine_first(newcols)
        newcols=categories['Weight'].str.extract('(?P<weight_value>[^ ]*)( \[(?P<drop_count>\d+)\])?',expand=True)
        del newcols[1]
        categories=categories.combine_first(newcols)
        # result.categories=categories[categories.cat_count.notnull()]
        result.categories=categories
        logging.debug("categories: \n%s",result.categories)
        final_weight=int(categories.set_index('Assignment Category').loc['Final']['Weight'])

        # Grades
        ## Line 8 contains student fields names
        result.student_fields=pandas.read_csv(self.file,sep='\t',skiprows=7,nrows=0).columns[:-1]
        logging.debug("result.student_fields: %s",result.student_fields)
        num_student_fields=len(result.student_fields)

        df = pandas.read_csv(self.file,skiprows=[0,1,2,3,5,6,7],sep='\t')
        bad_fields=df[:num_student_fields]
        colmap=dict(zip(bad_fields,result.student_fields))
        result._grades=df.rename(columns=colmap).dropna(how='any',axis=1)
        return result


class WebAssignGradeBook(object):

    def __init__(self):
        self._grades=pandas.DataFrame(columns=['Username','Fullname'])
        self.categories=pandas.DataFrame({'Assignment Category':['Final'],'Weight':[100]})
        self.date=date.today()

    @property
    def grades(self):
        return self._grades

# Decorator Pattern
class WagbDecorator(WebAssignGradeBook):

    def __init__(self,wagb=None):
        self._wagb=wagb
        # all Wagb methods/properties get passed to the component
        self.date=self._wagb.date
        self.categories=self._wagb.categories

    @property
    def grades(self):
        raise NotImplementedError


class WagbCorrectDiagnostic(WagbDecorator):
    """WebAssignGradeBook Decorator that rounds up the Quiz column to 100%,
    and recalculates the grades"""

    def roundup(self,colname):
        "round up column `colname` to 100% if positive"
        df=self._wagb.grades
        newcolname=colname + ' roundup'
        df[newcolname] = df.apply(lambda x: 100.0 if (x[colname] > 0) else 0.0,axis=1)
        df[colname] = df[newcolname]
        del df[newcolname]
        return df

    def recalculate(self):
        "recalculate the grades"
        df=self._wagb.grades
        # really should get category weights from the categories DataFrame
        cats=self.categories[self.categories.cat_count.notnull()]
        # logging.debug("cats: \n%s",cats)
        colnames=cats['Assignment Category'].tolist()
        logging.debug("colnames: %s",colnames)
        colweights=cats['weight_value'].tolist()
        def average(x):
            # logging.debug('x: %s',x)
            result=0
            for i,cat in enumerate(colnames):
                result+= colweights[i]*x[cat]
            return result
        df['Final'] = df.apply(average,axis=1)
        return df

    @property
    def grades(self):
        self.roundup('Quiz [1]')
        return self.recalculate()

class WagbAddDatedColumn(WagbDecorator):
    """WebAssignGradeBook Decorator that clones the "Final" column with
    the date (easy for importing to NYU Classes"""

    @property
    def grades(self):
        df=self._wagb.grades
        new_column_name = 'WebAssign import %s' % self.date
        df[new_column_name]=df['Final']
        # TODO: rearrange columns http://stackoverflow.com/q/13148429/297797
        return df



class NyuClassesGradebook(object):
    def __init__(self):
        "constructor"
        self.student_columns=['Student ID','Student Name']
        self._grades=pandas.DataFrame(columns=self.student_columns)

    @property
    def students(self):
        return self.grades.loc[:,self.student_columns]

    @property
    def grades(self):
        return self._grades

class NyucgbParser(object):
    "NYU Classes gradebook CSV file parser"

    def __init__(self,file=None):
        self.file=file

    def parse(self):
        gb=NyuClassesGradebook()
        if self.file is not None:
            gb._grades=pandas.read_csv(self.file)
        # TODO: parse file name for site id and date (why not?)
        return gb


class NyucgbDecorator(NyuClassesGradebook):
    "abstract decorator class for NyuClassesGradebook"

    def __init__(self,component=None):
        logging.debug("NyucgbDecorator: begin")
        self._component=component
        # all component properties that aren't overwritten
        # are passed to the component
        self.student_columns=self._component.student_columns

    @property
    def students(self):
        return self._component.students

    @property
    def grades(self):
        # Instead of raising a NotImplementedError,
        # we just use the identity decoration
        return self._component.grades


class NyucgbDecorator(NyucgbDecorator):
    "Decorates an NYU Classes gradebook by merging a WebAssign gradebook"

    def __init__(self,component=None,wagb=None):
        logging.debug("NyucgbDecorator constructor begin")
        super().__init__(component)
        self.wagb=wagb

    @property
    def grades(self):
        students=self.students
        wa_grades=self.wagb.grades
        # Merge attempt 1: NYU Classes Student ID = WebAssign Username
        m1=students.merge(wa_grades,left_on='Student ID',right_on='Username',how='left')
        # Merge attempt 2: NYU Classes Student Name = WebAssign Fullname
        m2=students.merge(wa_grades,left_on='Student Name',right_on='Fullname',how='left')
        # Merge attempt 3: NYU Classes Student ID = WebAssign Email local-part (before @)
        try:
            wa_grades['Email_localpart'],wa_grades['Email_domain'] = wa_grades.Email.str.split('@',1).str
            m3=students.merge(wa_grades,left_on='Student ID',right_on='Email_localpart')
            del m3['Email_localpart'], m3['Email_domain']
        except AttributeError:
            logging.warning("Email addresses not in WebAssign GradeBook.  Cannot attempt email matching.")
            m3=m1
        # I don't think we are supposed to alter the object here.
        # Just pass the result
        return m1.combine_first(m2).combine_first(m3)

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


@click.command()
@click.argument('wagb_file',
    type=click.Path(exists=True),metavar='WEBASSIGN_GRADEBOOK_FILE')
@click.argument('nyucgb_file',
    type=click.Path(exists=True),metavar='NYU_CLASSES_GRADEBOOK_FILE')
@click.option('-o','--output',
    type=click.File('w'),
    help='write to this file (use - for stdout)'
)
@click.option('-d','--debug',is_flag=True,default=False,help='print lots of debugging statments')
@click.option('-v','--verbose',is_flag=True,default=False,help="Be verbose")
def wagb_to_nyucgb(wagb_file, nyucgb_file, output, debug, verbose):
    """Merge a WebAssign GradeBook with an NYU Classes Gradebook file
    
    The first argument is the path to a downloaded WebAssign GradeBook. 
    From any WebAssign page, select **Tasks > Download Manager** and 
    select the desired class.  Then click the "GradeBook" button.

    Make sure the "email address" checkbox is ticked.  This helps match
    students from the two files.  Select the *Tab-Delimited Text* file option,
    then click "Download".  You'll get the tab-separated file in the window;
    save it anwywhere you like.  The default file name is something like
    `gradebook_3242351525.txt`.

    The second argument is an NYU Classes Gradebook file.  In NYU Classes,
    click "Import Grades" then "Download Spreadsheet Template as CSV".  
    The default filename is something like "gradebook-e5423452125.csv". 

    Pass the name of an output file to save to that file.  The default
    is to save to a file of the form `WebAssign_yyyy-mm-dd.csv`.  If you
    want to pipe the output, pass `-o -` on the command line.

  
    """
    logging.basicConfig(level=(logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)))
    wagb=WagbParser(wagb_file).parse()
    nyucgb=NyucgbParser(nyucgb_file).parse()
    nyucgb2=NyucgbDecorator(nyucgb,wagb)
    if output is None:
        output = open("WebAssign_%s.csv" % wagb.date.strftime('%Y-%m-%d'),'w')
    nyucgb2.grades.set_index('Student ID').to_csv(output)



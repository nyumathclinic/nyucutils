=====
Usage
=====

To use NYU Classes utilities in a project::

    import nyucutils


Roster and Gradebook Munging
============================

A *Roster* is a list of students.  A *Gradesheet* is a list of graded items,
indexed by students.  A *Gradebook* is the complete set of graded items for
an entire rosters.  Maybe?

Still not decided about this.

Importing WebAssign scores to NYU Classes
-----------------------------------------

Common use case:  You have a set of scores on WebAssign.  You need to import
the average into NYU Classes.  The exported GradeBook CSV file has a column
"Final" which needs to be renamed to something descriptive like "WebAssign
import as of 2017-02-24".  Also, the WebAssign CSV file needs to be converted
to a CSV format suitable for importing to NYU Classes.  This includes zeroes
for students who are on the NYU Classes roster but don't have grades on the
WebAssign roster (not as likely as in other scenarios).

Usage::

    from nyucutils.vendors import webassign, nyu_classes

    gradesheet = WebAssignGradeBook.from_csv('file.csv')
    gradebook = NyuClassesGradebook.from_csv('gradebook-2984723042.csv')
    gradebook.import(gradesheet)
    gradebook.to_csv('newgb.csv')

:code:`WebAssignGradeBook.from_csv(class,file)` is a class factory method.
It can accept strings (assumed to be paths) or file-like objects.
:code:`NyuClassesGradebook.to_csv(self,file)` is an object method, also
accepting strings or FLOs.

Then import to NYU Classes via web.

Can this work?  :code:`NyucGradebook.import(self,gradesheet)` gets a
:code:`NyucgbImporter` object and calls the :code:`import` method::

    from nyucutils.vendors import nyu_classes

    class NyuClassesGradebook(object):

        # ...

        def import(self,gradesheet):
            importer = NyuClassesGradebook.importer(self,gradesheet)
            importer.import()

The :code:`NyuClassesGradebook.importer` class function looks up an
Importer class based on the classes of :code:`gradesheet`.   Then::

    class NyucgbImporterWebassign(NyucgbImporter)

        def __init__(self,gradebook=None,gradesheet=None):
            self._gradebook = gradebook
            self._gradesheet = gradesheet

        def import(self):
            self._gradebook.merge(self.munge())


Feels like the Strategy pattern.

`This SESE answer`__ says to use class methods for factories.

__ http://softwareengineering.stackexchange.com/a/166715/149470

Importing homework scores from Gradescope
-----------------------------------------

Usage::

    from nyucutils.vendors.gradescope import GradescopeGradesheet
    from nyucutils.vendors.nyu_classes import NYUClassesGradebook

    gradesheet = GradescopeGradesheet.from_csv('Homework 3.csv')
    gradebook = NyuClassesGradebook.from_csv('gradebook-2984723042.csv')
    gradebook.import(gradesheet)
    gradebook.to_csv('newgb.csv')


Importing attendance scores from Attendance2
--------------------------------------------

In this case we could import from sqlite, or from any of the CSV export
formats.  sqlite import is more flexible but harder.

Here we also see the need to add a column summarizing the scores.  The options
are to register a callback function computing the summary column, or extend
the gradebook as a decorator.

Usage::

    from nyucutils.vendors.attendance2 import Attendance2Gradebook
    from nyucutils.vendors.nyu_classes import NYUClassesGradebook

    def summarize(gradesheet,graderec):
        # do something.  Access to each student's data as a record.
        # But also to the entire gradesheet (so you can find, say, the
        # z-score)
        pass

    gradebook = NyuClassesGradebook.from_csv('gradebook-2984723042.csv')
    grades = Attendance2Gradebook.from_sqlite('class.sqlite')
    grades.add_summary(summarize,name='Attendance Score 2017-02-27')
    gradebook.import(grades)
    gradebook.to_csv('newgb.csv',columns=['Attendance Score 2017-02-27'])




Importing attendance scores from a Google Quiz spreadsheet
----------------------------------------------------------

ditto


File Exchange interface
=======================

Uploading a set of files, indexed by user::

    from nyucutils import Site

    site = Site(site_id="dsfadsfa")
    for (user,file,dest) in manifest:
        site.file_exchange.upload(user,file,dest)

So `nyucutils.Site` is a facade for all the tools.

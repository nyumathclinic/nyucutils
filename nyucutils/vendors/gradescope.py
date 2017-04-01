#!/opt/local/bin/python
import csv
import logging
import os

import click


@click.command()
@click.argument('nyucgbfile')
@click.option('-d', '--debug', is_flag=True, default=False,
              help='print lots of debugging statements')
@click.option('-v', '--verbose', is_flag=True, default=False,
              help="Be verbose")
def munge(nyucgbfile, debug, verbose):
    """ Convert an NYU Classes Gradebook file to a Gradescope roster file"""
    with open(nyucgbfile) as csvfile:
        reader = csv.DictReader(csvfile)
        click.echo("Full Name,Email,NetID")
        for row in reader:
            lastname, firstname = row['Student Name'].split(', ')
            netId = row['Student ID']
            email = netId + '@nyu.edu'
            click.echo("%s %s,%s,%s" % (firstname, lastname, email, netId))


@click.command()
@click.argument('gsgbfile',
                type=click.Path(exists=True),
                metavar='GRADESCOPE_FILE')
@click.argument('max_pts')
@click.option('-o', '--output',
              type=click.File('w'),
              help='write to this file (use - for stdout)')
@click.option('-d', '--debug', is_flag=True, default=False,
              help='print lots of debugging statements')
@click.option('-v', '--verbose', is_flag=True, default=False,
              help="Be verbose")
def gs2nyuc(gsgbfile, max_pts, output, debug, verbose):
    """Convert a Gradescope gradebook file to a NYU Classes gradebook file"""
    logging.basicConfig(level=(logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)))
    assignment_name = gsgbfile.split('_scores')[0]
    assignment_name = assignment_name.replace('_', ' ')
    with open(gsgbfile) as csvfile:
        reader = csv.DictReader(csvfile)
        if output is None:
            (root, ext) = os.path.splitext(gsgbfile)
            output_path = root + '.nyucgb' + ext
            output = open(output_path, 'w')
        writer = csv.writer(output)
        writer.writerow(["Student ID",assignment_name])
        for row in reader:
            if row['Total Score']:
                row['Percent'] = float(row['Total Score']) / float(max_pts) * 100
                writer.writerow([row['SID'], "%.2f " % row['Percent']])
        output.close()

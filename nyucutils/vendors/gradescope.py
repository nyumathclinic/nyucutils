#!/opt/local/bin/python
import click
import csv

@click.command()
# This doesn't do anything yet.
@click.option('--debug',default=False,help='Print lots of debugging statements')
@click.argument('nyucgbfile')
def munge(nyucgbfile,debug):
    with open(nyucgbfile) as csvfile:
        reader=csv.DictReader(csvfile)
        click.echo("Full Name,Email,NetID")
        for row in reader:
            lastname,firstname = row['Student Name'].split(', ')
            netId = row['Student ID']
            email = netId + '@nyu.edu'
            click.echo("%s %s,%s,%s" % (firstname,lastname,email,netId))

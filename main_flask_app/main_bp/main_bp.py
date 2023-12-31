from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required, current_user
from main_flask_app.dash_app_cycling import *
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField, TimeField, validators, ValidationError
import requests
import os
import csv
import json
from main_flask_app import db, db_dataset
from main_flask_app.models import Reports, cycle_parking_data, boroughs_list
from io import StringIO

main_bp = Blueprint('main_bp',
                    __name__,
                    template_folder="templates", static_folder="static")
basedir = os.path.abspath(os.path.dirname(__file__))
maindir = os.path.abspath(os.path.join(basedir, os.pardir))

# Querying dataset tables from the cycle_parking.db database and
# setting up variables/arrays for later use
all_boroughs_list = []
for x in db_dataset.query(boroughs_list.borough):
    all_boroughs_list.append(list(x))
all_boroughs_list = [
    element for nestedlist in all_boroughs_list for element in nestedlist]

corresponding_borough = []
feature_id_list = []
marker_data = []
for x in db_dataset.query(cycle_parking_data.feature_id,
                          cycle_parking_data.prk_cover,
                          cycle_parking_data.prk_secure,
                          cycle_parking_data.prk_locker,
                          cycle_parking_data.prk_cpt,
                          cycle_parking_data.borough,
                          cycle_parking_data.photo1_url,
                          cycle_parking_data.photo2_url,
                          cycle_parking_data.latitude,
                          cycle_parking_data.longitude):
    rack_type_converted = []
    for i in range(1, 4):
        if x[i] == "1":
            rack_type_converted.append("True")
        if x[i] == "0":
            rack_type_converted.append("False")
    each_row = {"feature_id": x[0],
                "prk_cover": rack_type_converted[0],
                "prk_secure": rack_type_converted[1],
                "prk_locker": rack_type_converted[2],
                "prk_cpt": x[4],
                "borough": x[5],
                "photo1_url": x[6],
                "photo2_url": x[7],
                "latitude": x[8],
                "longitude": x[9]
                }
    marker_data.append(each_row)
    feature_id_list.append(x[0])
    corresponding_borough.append(x[5])


# Classes for forms
# Creating new reports
class ReportForm(FlaskForm):
    report_rack_id = StringField("Rack ID", validators=[
        validators.Length(min=9, max=9), validators.DataRequired()])
    report_borough = StringField("Borough", validators=[
        validators.DataRequired()])
    report_date = DateField("Date", validators=[
        validators.DataRequired()])
    report_time = TimeField("Time", validators=[
        validators.DataRequired()])
    report_details = StringField("Report Details", validators=[
        validators.DataRequired(), validators.Regexp(r'^[\w.@+-]+$')])
    report_submit = SubmitField("Submit")


# Selecting a borough on the "Download Data" page
class BoroughForm(FlaskForm):
    report_borough = SelectField("Borough", validators=[
        validators.DataRequired()])


# Accessing reports page but only showing the reports for the
# logged-in user which they can then manage
@main_bp.route('/my_reports', methods=['POST', 'GET'])
@login_required
def my_reports():
    reports_table = Reports.query.order_by(
        Reports.report_date.desc(), Reports.report_time.desc())
    user_reports_count = Reports.query.filter_by(
        reporter_id=current_user.id).count()
    if request.method == "GET":
        return render_template('my_reports.html', reports_table=reports_table,
                               user_reports_count=user_reports_count)
    elif request.method == "POST":
        flash("Your reports have been updated.")
        return render_template('my_reports.html', reports_table=reports_table)


# On the personalised reports page, users can instantly edit report details
# from the table
@main_bp.route("/edit_report_details/<int:report_id>", methods=['POST'])
@login_required
def edit_report_details(report_id):
    if request.method == "POST":
        report_to_edit = Reports.query.filter_by(id=report_id).first()
        if report_to_edit.reporter_id == current_user.id:
            print('editable_details' + str(report_id))
            report_to_edit.report_details = request.form[
                'editable_details' + str(report_id)]
            db.session.commit()
            flash("Report details successfully edited.")
            return redirect(url_for("main_bp.my_reports"))
        else:
            flash(
                "There was an error editing the report details."
                "Please try again later.")
            return redirect(url_for("main_bp.my_reports"))


# On the personalised reports page, users can instantly delete reports from
# the table
@main_bp.route("/delete_report/<int:report_id>", methods=['POST'])
@login_required
def delete_report(report_id):
    if request.method == "POST":
        report_to_delete = Reports.query.filter_by(id=report_id).first()
        if report_to_delete.reporter_id == current_user.id:
            Reports.query.filter_by(id=report_id).delete()
            db.session.commit()
            flash("Report successfully deleted.")
            return redirect(url_for("main_bp.my_reports"))
        else:
            flash("There was an error deleting the report."
                  "Please try again later.")
            return redirect(url_for("main_bp.my_reports"))


# Viewing the dash statistics app (iframe src used on the html page)
@main_bp.route("/dash_statistics")
def dash():
    return render_template("dash_statistics.html")


# Viewing the API instructions page
@main_bp.route("/api")
def api_instructions_shortcut():
    return render_template("api_instructions.html")


# Instructions page on using the API
@main_bp.route("/api_instructions")
def api_instructions():
    return render_template("api_instructions.html")


# Viewing all reports by all users
@main_bp.route("/reports")
def reports_page():
    reports_table = Reports.query.order_by(Reports.report_date.desc(),
                                           Reports.report_time.desc())
    user_reports_count = Reports.query.count()
    return render_template("reports.html",
                           reports_table=reports_table,
                           user_reports_count=user_reports_count)


# Index page showing the main map from where reports can be created
@main_bp.route("/", methods=['POST', 'GET'])
def index():
    report_form = ReportForm()
    if request.method == "GET":
        return render_template('index.html',
                               markers_info=json.dumps(marker_data),
                               boroughs=all_boroughs_list,
                               report_form=report_form)
    elif request.method == "POST":  # report_form.validate_on_submit():
        reporter_id = current_user.id
        rack_id_flask = request.form['report_rack_id']
        borough_flask = request.form['report_borough']
        date_flask = request.form['report_date']
        time_flask = request.form['report_time']
        report_details_flask = request.form['report_details']

        new_report = Reports(reporter_id=reporter_id,
                             report_borough=borough_flask.title(),
                             rack_id=rack_id_flask,
                             report_date=date_flask,
                             report_time=time_flask,
                             report_details=report_details_flask)

        if (rack_id_flask.upper() in feature_id_list):
            index = feature_id_list.index((rack_id_flask).upper())
            if (borough_flask).lower() == (corresponding_borough[index]).lower():
                try:
                    db.session.add(new_report)
                    db.session.commit()
                    flash("Report created successfully.")
                    return redirect(url_for('main_bp.index'))
                except:
                    flash("There was an error submitting the report."
                          "Please try again later.")
                    return redirect(url_for('main_bp.index'))

            else:
                flash("Please ensure that borough is correct."
                      " Selecting the marker is the easiest way to fill out the form correctly.")
        else:
            flash("Please ensure that the rack ID "
                  "exists and is from the correct borough."
                  " Selecting the marker is the easiest way to fill out the form correctly.")
        return redirect(url_for('main_bp.index'))


# From the main reports page, it is possible to view all reports for a
# specific bike rack on another page
@main_bp.route("/specific_reports/<string:specific_rack_id>", methods=['GET'])
def specific_reports(specific_rack_id):
    if request.method == "GET":
        if specific_rack_id in feature_id_list:
            try:
                specific_reports_to_view = Reports.query.filter_by(
                    rack_id=specific_rack_id).order_by(
                    Reports.report_date.desc(),
                    Reports.report_time.desc())
                specific_report_count = specific_reports_to_view.count()
                specific_borough = specific_reports_to_view.first(
                ).report_borough
                try:
                    flash("You are now viewing reports"
                          " specifically for bike rack " + str(
                            specific_rack_id) + " (" + str(
                            specific_borough) + ").")
                    return render_template(
                        "specific_reports.html",
                        specific_reports_to_view=specific_reports_to_view,
                        specific_report_count=specific_report_count,
                        specific_rack_id=specific_rack_id,
                        specific_borough=specific_borough)
                except:
                    flash("There was an error getting the reports."
                          "Please try again later.")
                    return redirect(url_for("main_bp.reports_page"))
            except:
                flash("That bike rack has no theft reports."
                      "You have been returned to the reports page.")
                return redirect(url_for("main_bp.reports_page"))
        else:
            flash("A bike rack with that ID does not exist."
                  "You have been returned to the reports page.")
            return redirect(url_for("main_bp.reports_page"))


# Using the API, data from the SQL database is taken and
# then made downloadable for users
@main_bp.route("/download_data", methods=['GET', 'POST'])
def download_data():
    form = BoroughForm()
    if request.method == "GET":
        return render_template('download_data.html', form=form,
                               boroughs=all_boroughs_list)
    elif request.method == "POST":
        borough_selected = request.form['report_borough']
        reports_request = requests.get("http://localhost:5000/api/reports")
        reports_json = reports_request.json()
        reports_list = reports_json["report"]
        all_reports_count = len(reports_list)
        if all_reports_count > 0:
            if borough_selected == "All Boroughs":
                reports_filtered = reports_list
            else:
                count = 0
                reports_for_borough_only = []
                for x in reports_list:
                    if x["report_borough"] == borough_selected:
                        reports_for_borough_only.append(x)
                        count = count + 1
                if count > 0:
                    reports_filtered = reports_for_borough_only
                else:
                    flash("There are no related active reports in " +
                          borough_selected +
                          ". Try again later or select another option.")
                    return redirect(url_for("main_bp.download_data"))
        else:
            flash("There are no related active reports in "
                  + borough_selected
                  + ". Try again later or select another option.")
            return redirect(url_for("main_bp.download_data"))
        # Convert the reports data to a CSV string
        csv_data = StringIO()
        writer = csv.writer(csv_data)
        writer.writerow(['report_id', 'reporter_id', 'borough',
                         'date', 'time', 'details'])
        for report in reports_filtered:
            writer.writerow([report["id"],
                             report["reporter_id"],
                             report["report_borough"],
                             report["report_date"],
                             report["report_time"],
                             report["report_details"]])

        # Create a response with the CSV data and appropriate headers
        response_csv_file = make_response(csv_data.getvalue())
        response_csv_file.headers["Content-Type"] = "text/csv"
        response_csv_file.headers["Content-Disposition"] = (
            f"attachment; filename={borough_selected}_reports.csv")
        # Return the response for downloading the CSV file
        return response_csv_file

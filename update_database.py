from glob import glob
import database_tools as dt
import sys
import rotation_analysis_tools as rat
from sqlalchemy.exc import IntegrityError

def get_files(folder):
    return glob(folder + '/*.csv')

def get_modules(filelist):
    module_set = set(f.split('/')[1].split("_")[0] for f in filelist)
    return module_set

def get_scans(filelist):
    scan_set = set(f.split('/')[1].split('_Scan')[0] for f in filelist)
    return scan_set

def update_database():
    folder = 'sensor_scan_data/'

    filelist = get_files(folder)
    modules_to_insert = get_modules(filelist)
    scans_to_insert = get_scans(filelist)

    session, modules, scans = dt.get_session()

    for module_to_insert in modules_to_insert:
        try:
            session.add(modules(name=module_to_insert))
            session.commit()
        except IntegrityError as e:
            #already exists in database
            print("module already in DB")
            session.rollback()

    modules_from_db = dict([(iq.name, iq.id) for iq in session.query(modules)])

    for scan_to_insert in scans_to_insert:
        split_scan = scan_to_insert.split("_")
        scan_module = split_scan[0]
        scan_date = ("-").join(split_scan[1:4])
        scan_time = split_scan[4]
        scan_points = ["{}{}_ScanPoint{}.csv".format(folder, scan_to_insert, i) for i in range(1,5)]
        _, scan_measurement = rat.calculate_rotation(*scan_points)
        try:
            session.add(scans(moduleid=modules_from_db[scan_module],date=scan_date, time=scan_time, misalignment=scan_measurement))
            session.commit()
        except IntegrityError as e:
            print("scan already in DB")
            session.rollback()

    session.commit()
    session.close()

if __name__ == "__main__":
    update_database()
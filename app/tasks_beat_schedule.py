from celery import current_task
from flask import flash
from app import celery, db
from app.models import Task, JasperAccount, JasperCredential, User, RatePlan, RatePlanZone, RatePlanTierDataUsage, \
    RatePlanSMSUsage, RatePlanTierSMSUsage, RatePlanVoiceUsage, \
    RatePlanTierVoiceUsage, RatePlanDataUsage, RatePlanTierCost, SubscriberIdentityModule
from app.jasper import rest
from datetime import datetime


@celery.task()
def beat_schedule_check_api_connections():
    jasper_credentials = JasperCredential.query.all()
    for credential in jasper_credentials:
        for account in credential.jasper_accounts:
            response = rest.echo(credential.username, credential.api_key, account.resource_url)

            datetime_stamp = datetime.now()
            credential.last_check = datetime_stamp
            account.last_check = datetime_stamp

            if response[0] == "error":
                db.session.commit()
            elif response[0] == "data":
                credential.last_confirmed = datetime_stamp
                account.last_confirmed = datetime_stamp
                db.session.commit()


@celery.task()
def beat_schedule_check_sims_connections():
    jasper_account = JasperAccount.query.all()
    for accounts in jasper_account:
        for sims in accounts.subscriber_identity_modules:
            print(sims)
            print(accounts.jasper_credentials)

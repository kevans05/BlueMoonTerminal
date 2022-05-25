from app import celery, db
from app.models import JasperAccount, JasperCredential, User, RatePlan, RatePlanZone, RatePlanTierDataUsage, \
    RatePlanSMSUsage, RatePlanTierSMSUsage, RatePlanVoiceUsage, \
    RatePlanTierVoiceUsage, RatePlanDataUsage, RatePlanTierCost, SubscriberIdentityModule, DataUsageToDate
# from app.tasks import finish_task
from app.jasper import rest
from datetime import datetime
from celery import current_task


def beat_scheduled_task_add_to_database(task_name):
    job = current_task
    print(job.request.id)
    # task = TaskJasperAccounts(id=active_tasks.id, name=task_name, description="testing the users credentials",
    #             user=current_user)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(3600.0, beat_schedule_check_sims_connections.s(),
                             name='add-every-1-hour')

    sender.add_periodic_task(60.0, beat_schedule_check_api_connections.s(),
                             name='add-every-minute')

    sender.add_periodic_task(600.0, beat_schedule_check_usage_a.s(),
                             name='add-every-10-minutes')


@celery.task()
def beat_schedule_check_api_connections():
    jasper_credentials = JasperCredential.query.all()
    beat_scheduled_task_add_to_database('beat_schedule_check_api_connections')
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
    beat_scheduled_task_add_to_database('beat_schedule_check_sims_connections')
    for accounts in jasper_account:
        for sim in accounts.subscriber_identity_modules:
            response = rest.get_iccid_info(accounts.jasper_credentials[0].username,
                                           accounts.jasper_credentials[0].api_key,
                                           accounts.resource_url, sim.iccid)
            if response[0] == "data":
                SubscriberIdentityModule.query.filter_by(iccid=sim.iccid). \
                    update({'imei': response[1]['imei'], 'imsi': response[1]['imsi'], 'msisdn': response[1]['msisdn'],
                            'status': response[1]['status'],
                            'date_activated': rest.convert_datetime(response[1]['dateActivated']),
                            'date_added': rest.convert_datetime(response[1]['dateAdded']),
                            'date_updated': rest.convert_datetime(response[1]['dateUpdated']),
                            'date_shipped': rest.convert_datetime(response[1]['dateShipped']),
                            'communication_plan': response[1]['communicationPlan'],
                            'account_id': response[1]['accountId'], 'fixed_ip_address': response[1]['fixedIPAddress'],
                            'operator_custom1': response[1]['operatorCustom1'],
                            'operator_custom2': response[1]['operatorCustom1'],
                            'operator_custom3': response[1]['operatorCustom3'],
                            'operator_custom4': response[1]['operatorCustom4'],
                            'account_custom1': response[1]['accountCustom1'],
                            'account_custom2': response[1]['accountCustom2'],
                            'account_custom3': response[1]['accountCustom3'],
                            'account_custom4': response[1]['accountCustom4'],
                            'account_custom5': response[1]['accountCustom5'],
                            'account_custom6': response[1]['accountCustom6'],
                            'account_custom7': response[1]['accountCustom7'],
                            'account_custom8': response[1]['accountCustom8'],
                            'account_custom9': response[1]['accountCustom9'],
                            'account_custom10': response[1]['accountCustom10'],
                            'customer_custom1': response[1]['customerCustom1'],
                            'customer_custom2': response[1]['customerCustom2'],
                            'customer_custom3': response[1]['customerCustom3'],
                            'customer_custom4': response[1]['customerCustom4'],
                            'customer_custom5': response[1]['customerCustom5'], 'sim_notes': response[1]['simNotes'],
                            'euiccid': response[1]['euiccid'], 'device_id': response[1]['deviceID'],
                            'modem_id': response[1]['modemID'],
                            'global_sim_type': response[1]['globalSimType'], 'mec': response[1]['mec']})
                db.session.commit()


@celery.task()
def beat_schedule_check_usage_a():
    jasper_account = JasperAccount.query.all()
    datetime_stamp = datetime.now()
    for accounts in jasper_account:
        for sims in accounts.subscriber_identity_modules:
            response = rest.get_cycle_to_date(accounts.jasper_credentials[0].username,
                                              accounts.jasper_credentials[0].api_key,
                                              accounts.resource_url, sims.iccid)
            if response[0] == "data":
                subscriber_identity_module = SubscriberIdentityModule.query.filter_by(iccid=sims.iccid).first()

                subscriber_identity_module.data_usage_to_date.append(
                    DataUsageToDate(ctdDataUsage=response[1]['ctdDataUsage'], ctdSMSUsage=response[1]['ctdSMSUsage'],
                                    ctdVoiceUsage=response[1]['ctdVoiceUsage'], date_updated=datetime_stamp))
                db.session.commit()


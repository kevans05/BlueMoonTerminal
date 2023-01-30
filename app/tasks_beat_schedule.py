import logging

import app
from app import celery, db
from app.models import JasperAccount, JasperCredential, DataUsageToDate, RatePlan, RatePlanZone, RatePlanDataUsage, \
    RatePlanTierDataUsage, RatePlanSMSUsage, RatePlanTierSMSUsage, RatePlanVoiceUsage, RatePlanTierVoiceUsage, \
    RatePlanTierCost, SubscriberIdentityModule, AssociationBetweenSubscriberIdentityModuleRatePlan
from app.jasper import rest
from datetime import datetime


#converts the function
def metric_to_value(metric):
    match metric:
        case 'B':
            return 1
        case 'kB':
            return 1000
        case 'MB':
            return 1000 ** 2
        case 'GB':
            return 1000 ** 3
        case 'TB':
            return 1000 ** 4
        case 'PB':
            return 1000 ** 5
        case 'EB':
            return 1000 ** 6
        case 'ZB':
            return 1000 ** 7
        case 'YB':
            return 1000 ** 8


def get_sims_for_account_list(account_id):
    account = JasperAccount.query.filter_by(id=account_id).first()
    sim_list = []
    for sims in account.subscriber_identity_modules:
        data_to_date = DataUsageToDate.query.filter_by(sim_id=sims.id).order_by(
            DataUsageToDate.date_updated.desc()).first()
        if data_to_date:
            sim_list.append((sims.iccid, data_to_date.ctdDataUsage, data_to_date.zones))
        else:
            sim_list.append((sims.iccid, 0, None))
    return sim_list


def get_rate_plans_for_account_list(account):
    return db.session.query(RatePlan).filter_by(jasper_account_id=account, active = True).outerjoin(RatePlanZone, RatePlan.id ==
                                                                                        RatePlanZone.rate_plan_id).add_entity(
        RatePlanZone).outerjoin(
        RatePlanDataUsage, RatePlanZone.id ==
                           RatePlanDataUsage.rate_plan_zone_id).add_entity(RatePlanDataUsage).outerjoin(
        RatePlanTierDataUsage, RatePlanDataUsage.id ==
                               RatePlanTierDataUsage.rate_plan_data_usages_id).add_entity(
        RatePlanTierDataUsage).outerjoin(
        RatePlanSMSUsage, RatePlanZone.id ==
                          RatePlanSMSUsage.rate_plan_zones_id).add_entity(RatePlanSMSUsage).outerjoin(
        RatePlanTierSMSUsage, RatePlanSMSUsage.id ==
                              RatePlanTierSMSUsage.rate_plan_sms_usages_id).add_entity(
        RatePlanTierSMSUsage).outerjoin(
        RatePlanVoiceUsage, RatePlanZone.id ==
                            RatePlanVoiceUsage.rate_plan_zones_id).add_entity(RatePlanVoiceUsage).outerjoin(
        RatePlanTierVoiceUsage, RatePlanVoiceUsage.id ==
                                RatePlanTierVoiceUsage.rate_plan_voice_usages_id).add_entity(
        RatePlanTierVoiceUsage).outerjoin(RatePlanTierCost, RatePlan.id ==
                                          RatePlanTierCost.rate_plan_id).add_entity(RatePlanTierCost).order_by(
        RatePlanDataUsage.included_data.desc())


#function checks to see if the API connection is able to be made

@celery.task(bind=True)
def beat_schedule_check_api_connections(self):
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


@celery.task(bind=True)
def beat_schedule_check_sims_connections(self):
    jasper_account = JasperAccount.query.all()
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


@celery.task(bind=True)
def beat_schedule_check_usage_a(self):
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


@celery.task(bind=True)
def beat_schedule_optimize_by_accounts(self):
    jasper_account = JasperAccount.query.all()
    for account in jasper_account:
        # beat_schedule_optimize_account.apply_async(kwargs={"account": account.id})
        beat_schedule_optimize_account.apply_async(kwargs={"account": account.id})
        # beat_schedule_optimize_by_accounts.apply_async(object=)


@celery.task()
def beat_schedule_optimize_account(**kwargs):
    account = kwargs['account']
    rate_plans = get_rate_plans_for_account_list(
        account).all()
    sims = sorted(get_sims_for_account_list(account), key=lambda data: data[1], reverse=True)

    optimize_by_rate_plan(account=account, rate_plans=rate_plans, sims=sims)



def optimize_by_rate_plan(account, rate_plans, sims):
    rate_plan = rate_plans[0]
    logging.critical(rate_plan[0].name)
    included_data = metric_to_value(rate_plan[2].included_data_unit) * rate_plan[2].included_data
    logging.debug("Included data " + str(included_data))
    plan_data = 0
    number_of_plan = 0
    sims_in_plan = []
    # as long as its not the last rateplan in the system sort the system
    if len(rate_plans) > 1:
        for sim in sims:
            logging.debug(sim)
            if sim[1] > included_data or ((number_of_plan * included_data) - plan_data) < 0:
                logging.debug(plan_data)
                logging.debug((number_of_plan * included_data))
                logging.debug(((number_of_plan * included_data) - plan_data))
                plan_data += sim[1]
                number_of_plan += 1
                sims_in_plan.append(sim)
                beat_schedule_add_target_subscriber_identify_module_to_rate_plan(rate_plan, sim)
                beat_schedule_upload_to_jasper(account, rate_plan, sim)
            else:
                break
        res = [i for i in sims if i not in sims_in_plan]
        optimize_by_rate_plan(account, rate_plans[1:], res)
    elif len(rate_plans) == 1:  # if it is the last rateplan in the system, add them all remaining to the last plan
        sims_in_plan.extend(sims)
        sims.clear()
        for sim in sims_in_plan:
            logging.critical(sim)
            beat_schedule_add_target_subscriber_identify_module_to_rate_plan(rate_plan,sim)
            beat_schedule_upload_to_jasper(account, rate_plan, sim)



#logs the upload change in rate  plan, gets the targert SIM from the database, will add the current rateplan assosaition
def beat_schedule_add_target_subscriber_identify_module_to_rate_plan(rate_plan, sim):


    target_subscriber_identify_module = SubscriberIdentityModule.query.filter_by(iccid=sim[0]).first()
    association_between_subscriber_identity_module_rate_plan_object = \
        AssociationBetweenSubscriberIdentityModuleRatePlan()
    association_between_subscriber_identity_module_rate_plan_object.rate_plans = rate_plan[0]
    target_subscriber_identify_module.rate_plans.append \
        (association_between_subscriber_identity_module_rate_plan_object)
    db.session.commit()


#the function that uploads the data to the jasper website
def beat_schedule_upload_to_jasper(account_id, rate_plan, sim):
    account = JasperAccount.query.filter_by(id=account_id).first()
    rest.update_iccid_details(account.jasper_credentials[0].username,
                              account.jasper_credentials[0].api_key,
                              account.resource_url, sim[0], {'ratePlan': rate_plan[0].name})


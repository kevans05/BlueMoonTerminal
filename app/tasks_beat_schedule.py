from app import celery, db
from app.models import JasperAccount, JasperCredential, DataUsageToDate, RatePlan, RatePlanZone, RatePlanDataUsage, \
    RatePlanTierDataUsage, RatePlanSMSUsage, RatePlanTierSMSUsage, RatePlanVoiceUsage, RatePlanTierVoiceUsage, \
    RatePlanTierCost, SubscriberIdentityModule, AssociationBetweenSubscriberIdentityModuleRatePlan
from app.jasper import rest
from datetime import datetime
import sys

# @celery.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(3600.0, beat_schedule_check_sims_connections.s(),
#                              name='add-every-1-hour')
#     sender.add_periodic_task(60.0, beat_schedule_check_api_connections.s(),
#                              name='add-every-minute')
#     sender.add_periodic_task(600.0, beat_schedule_check_usage_a.s(),
#                              name='add-every-10-minutes')

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


def get_sims_for_account_list(account):
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
    return db.session.query(RatePlan).filter_by(jasper_account_id=account.id).outerjoin(RatePlanZone, RatePlan.id ==
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


# @celery.task(bind=True)
# def beat_schedule_check_usage_b(self):
#     # gets a list of all jasper accounts
#     jasper_account = JasperAccount.query.all()
#     # goes threw the list of accounts
#     for account in jasper_account:
#         # makes a list of all the sims in the database
#         subscriber_identity_modules_iccid = [subscriber_identity_modules.iccid for subscriber_identity_modules in
#                                              account.subscriber_identity_modules]
#         for rate_plan in account.rate_plans:
#             list_of_iccid = rest.get_usage_by_rate_plan(account.jasper_credentials[0].username,
#                                                         account.jasper_credentials[0].api_key, account.resource_url,
#                                                         rate_plan.name)
#             if list_of_iccid[0] == "data":
#                 for iccid in list_of_iccid[1]:
#                     if iccid['iccid'] in subscriber_identity_modules_iccid:
#                         subscriber_identity_modules_iccid.remove(iccid['iccid'])
#                         subscriber_identity_module = SubscriberIdentityModule.query.filter_by(
#                             iccid=iccid['iccid']).first()
#                         print(subscriber_identity_module)
#                         if subscriber_identity_module is None:
#                             print("RAN")
#                             subscriber_identity_module = SubscriberIdentityModule(iccid=iccid['iccid'])
#                             jasper_account.subscriber_identity_modules.append(subscriber_identity_module)
#                             print("RAN 2")
#                         print("RAN 3")
#                         subscriber_identity_module.data_usage_to_date.append(
#                             DataUsageToDate(ctdDataUsage=iccid['dataUsage'], zones=iccid['zone'],
#                                             ctdSMSUsage=iccid['smsMOUsage'] + iccid['smsMTUsage'],
#                                             ctdVoiceUsage=iccid['voiceMOUsage'] + iccid['voiceMTUsage'],
#                                             date_updated=iccid['date_updated']))
#                         print("RAN 4")
#                         db.session.commit()
#                         print("RAN 5")
#                     else:
#                         print("RAN 6")
#                         account.subscriber_identity_modules.append(SubscriberIdentityModule(iccid=iccid['iccid']))
#                         print("RAN 7")
#                         db.session.commit()
#
#         for iccid in subscriber_identity_modules_iccid:
#             subscriber_identity_module = SubscriberIdentityModule.query.filter_by(iccid=iccid).first()
#             subscriber_identity_module.data_usage_to_date.append(
#                 DataUsageToDate(ctdDataUsage=0,
#                                 ctdSMSUsage=0,
#                                 ctdVoiceUsage=0,
#                                 date_updated=datetime.now()))
#             db.session.commit()

@celery.task(bind=True)
def beat_schedule_organize_sims_and_rates(self):
    jasper_account = JasperAccount.query.all()
    for account in jasper_account:
        rate_plans = get_rate_plans_for_account_list(
            account)
        sims = sorted(get_sims_for_account_list(account), key=lambda data: data[1], reverse=True)
        sumof = 0
        sumofsims = len(sims)
        for count, rate_plan in enumerate(rate_plans):
            included_data = metric_to_value(rate_plan[2].included_data_unit) * rate_plan[2].included_data
            plan_data = 0
            number_of_plan = 0
            sims_in_plan = []
            for sim in sims:
                if sim[1] > included_data or plan_data > number_of_plan*included_data or rate_plans.count() - 1 == count:
                    plan_data += sim[1]
                    number_of_plan += 1
                    sims_in_plan.append(sim)
                    sims.remove(sim)
                    sumofsims -= 1
                    p = SubscriberIdentityModule.query.filter_by(iccid=sim[0]).first()
                    a = AssociationBetweenSubscriberIdentityModuleRatePlan()
                    a.rate_plans = rate_plan[0]
                    p.rate_plans.append(a)
                    db.session.commit()
                    print(sim[0])
                    print(rest.update_iccid_details(account.jasper_credentials[0].username,
                                           account.jasper_credentials[0].api_key,
                                           account.resource_url, sim[0], {'ratePlan': rate_plan[0].name}))
                else:
                    break


            print("-@"*100 + "-")
            print("Plan Name: {}".format(rate_plan[0].name))
            print("-> Per Subscriber Charge: {}".format(rate_plan[8].per_subscriber_charge))
            print("-> Per Subscriber Data: {}".format(rate_plan[2].included_data))
            print("-- SIMS Left: {}".format(sumofsims))
            print("-^"*100 + "-")
            print("-->Number of Subscribers: {}".format(len(sims_in_plan)))
            print("-->Rate Charge: {}".format(len(sims_in_plan)*rate_plan[8].per_subscriber_charge))
            print("-->Rate Data Included: {}".format(len(sims_in_plan) * included_data))
            print("-->Data Used: {}".format(sum(x[1] for x in sims_in_plan)))
            print("-->Delta: {}".format(sum(x[1] for x in sims_in_plan) - len(sims_in_plan) * included_data))
            sumof += len(sims_in_plan)*rate_plan[8].per_subscriber_charge
            print("--" * 100 + "-")
        print(sumof)





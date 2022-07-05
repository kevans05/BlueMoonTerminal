from app import celery, db
from app.models import JasperAccount, JasperCredential, SubscriberIdentityModule, DataUsageToDate, RatePlan, \
    RatePlanZone, RatePlanDataUsage, RatePlanTierDataUsage, RatePlanSMSUsage, RatePlanTierSMSUsage, RatePlanVoiceUsage, \
    RatePlanTierVoiceUsage, RatePlanTierCost
from app.jasper import rest
from datetime import datetime


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
                            RatePlanTierCost.rate_plan_id).add_entity(RatePlanTierCost)


def bisection_sort(sims, plan):
    included_data = metric_to_value(plan[2].included_data_unit) * plan[2].included_data
    middle_index = int(len(sims)/2)
    sum_of_account = middle_index * included_data - sum(j for i, j, k in sims[:middle_index])
    print(plan[0].name)
    print("sum of account: {diffrence}".format(diffrence=sum_of_account))
    print("data left: {left}".format(left=included_data*middle_index))
    print("delta {delta}".format(delta=(sum_of_account - included_data*middle_index)))
    print("delta {delta}".format(delta=(sum_of_account - included_data * middle_index)))
    print(0 < sum_of_account-middle_index*included_data < included_data)
    print(0 > sum_of_account-middle_index*included_data < included_data)
    print(0 < sum_of_account - middle_index * included_data > included_data)
    if 0 < sum_of_account-middle_index*included_data < included_data:
        print("pass")
        return sims[:middle_index]
    elif 0 > sum_of_account-middle_index*included_data < included_data:
        print("rais {value}".format(value=int(middle_index*1.5)))
        return bisection_sort(sims[int(middle_index*1.5):], plan)
    elif 0 < sum_of_account - middle_index * included_data > included_data:
        print("Lower {value}".format(value=int(middle_index*.5)))
        return bisection_sort(sims[:int(middle_index*.5)], plan)
    # is_plan_greater_then_highest_sim = sims[0] >= included_data
    #
    # if () or (middle_index * included_data - sum(j for i, j, k in sims[:middle_index]) <= 0):
    #     return sims[:middle_index]
    # # elif sims[0] > included_data and sum(j for i, j, k in sims[:middle_index]) < included_data*middle_index:
    # #

def sort_sims_by_data(sims, rates):
    sims = sorted(sims, key=lambda data: data[1], reverse=True)
    rates = sorted(rates, key=lambda data: data[2].included_data, reverse=True)
    for plan in rates:
        #print(plan[0].name, plan[2].included_data, plan[1], plan[8].per_subscriber_charge)
        bisection_sort(sims, plan)

        #included_data = metric_to_value(plan[2].included_data_unit) * plan[2].included_data
        #number_of_data_accounts = 0
        #total_included_data = 0
        # print(plan[0].name)
        # for device in sims:
        #     # print(device[1])
        #     if (device[1] >= metric_to_value(plan[2].included_data_unit) or (
        #             number_of_data_accounts * included_data - total_included_data) <= 0):
        #         number_of_data_accounts = number_of_data_accounts + 1
        #         total_included_data = total_included_data + device[1]
        #         print(device)
        #         sims.remove(device)
        #     else:
        #         break
        # print(number_of_data_accounts)
        # print(total_included_data)
        # print("*" * 100)


def sort_sims_by_voice(sims, rates):
    return


def sort_sims_by_sms(sims, rates):
    return


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
def beat_schedule_check_usage_b(self):
    # gets a list of all jasper accounts
    jasper_account = JasperAccount.query.all()
    # goes threw the list of accounts
    for account in jasper_account:
        # makes a list of all the sims in the database
        subscriber_identity_modules_iccid = [subscriber_identity_modules.iccid for subscriber_identity_modules in
                                             account.subscriber_identity_modules]
        for rate_plan in account.rate_plans:
            list_of_iccid = rest.get_usage_by_rate_plan(account.jasper_credentials[0].username,
                                                        account.jasper_credentials[0].api_key, account.resource_url,
                                                        rate_plan.name)
            if list_of_iccid[0] == "data":
                for iccid in list_of_iccid[1]:
                    print(iccid['iccid'])
                    subscriber_identity_modules_iccid.remove(iccid['iccid'])
                    subscriber_identity_module = SubscriberIdentityModule.query.filter_by(iccid=iccid['iccid']).first()
                    if subscriber_identity_module is None:
                        subscriber_identity_module = SubscriberIdentityModule(iccid=iccid['iccid'])
                        jasper_account.subscriber_identity_modules.append(subscriber_identity_module)
                    subscriber_identity_module.data_usage_to_date.append(
                        DataUsageToDate(ctdDataUsage=iccid['dataUsage'], zones=iccid['zone'],
                                        ctdSMSUsage=iccid['smsMOUsage'] + iccid['smsMTUsage'],
                                        ctdVoiceUsage=iccid['voiceMOUsage'] + iccid['voiceMTUsage'],
                                        date_updated=iccid['date_updated']))
                    db.session.commit()

        for iccid in subscriber_identity_modules_iccid:
            subscriber_identity_module = SubscriberIdentityModule.query.filter_by(iccid=iccid).first()
            subscriber_identity_module.data_usage_to_date.append(
                DataUsageToDate(ctdDataUsage=0,
                                ctdSMSUsage=0,
                                ctdVoiceUsage=0,
                                date_updated=datetime.now()))
            db.session.commit()


@celery.task(bind=True)
def beat_schedule_organize_sims_and_rates(self):
    jasper_account = JasperAccount.query.all()
    for account in jasper_account:
        sims = get_sims_for_account_list(account)
        rate_plans = get_rate_plans_for_account_list(account)
        sort_sims_by_data(sims, rate_plans)

    # print(sorted(sim_list, key=lambda student: student[1], reverse=True))
    # for x in RatePlan.query.filter_by(jasper_account_id=accounts.id).all():
    #     print(dir(x))
    #     for y in x.rate_plan_zones:
    #         print(y.zone_name)

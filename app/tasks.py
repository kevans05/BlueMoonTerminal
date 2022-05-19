from celery import current_task
from flask import flash
from app import celery, db
from app.models import Task, JasperAccount, JasperCredential, User, RatePlan, RatePlanZone, RatePlanTierDataUsage, \
    RatePlanSMSUsage, RatePlanTierSMSUsage, RatePlanVoiceUsage, \
    RatePlanTierVoiceUsage, RatePlanDataUsage, RatePlanTierCost, SubscriberIdentityModule
from app.jasper import rest
from datetime import datetime


def finish_task():
    job = current_task
    task = Task.query.filter_by(id=job.request.id).first()
    task.complete = True
    db.session.commit()


def jasper_true_or_false(toChange):
    if toChange == 'true':
        return True
    else:
        return False


@celery.task()
def check_api_connections():
    jasper_credentials = JasperCredential.query.all()
    for credential in jasper_credentials:
        datetime_stamp = datetime.now()
        credential.last_check = datetime_stamp
        for account in credential.jasper_accounts:
            account.last_check = datetime_stamp
            response = rest.echo(credential.username, credential.api_key, account.resource_url)
            if response[0] == "error":
                db.session.commit()
            elif response[0] == "data":
                credential.last_confirmed = datetime_stamp
                account.last_confirmed = datetime_stamp
                db.session.commit()


@celery.task()
def new_api_connection(username, api_key, resource_url, current_user_id):
    response = rest.echo(username, api_key, resource_url)
    if response[0] == "error":
        flash("API Connection Error")
    elif response[0] == "data":
        user = User.query.filter_by(id=current_user_id).first()
        jasper_credential = JasperCredential.query.filter_by(api_key=api_key, username=username).first()
        if jasper_credential is None:
            jasper_credential = JasperCredential(username=username, api_key=api_key, users=user)
        jasper_credential.last_check = datetime.now()
        jasper_credential.last_confirmed = datetime.now()
        jasper_account = JasperAccount.query.filter_by(resource_url=resource_url).first()
        if jasper_account is None:
            jasper_credential.jasper_accounts.append(JasperAccount(resource_url=resource_url, last_check = datetime.now(), last_confirmed = datetime.now()))
        else:
            jasper_account.last_check = datetime.now()
            jasper_account.last_confirmed = datetime.now()
        db.session.add(jasper_credential)
        db.session.commit()
    finish_task()


@celery.task()
def new_rate_plans(username, api_key, resource_url):
    response = rest.get_rate_plan(username, api_key, resource_url)
    if response == "error":
        flash("rate plan download Error")
    else:
        for plans in response:
            rate_plan = RatePlan.query.filter_by(version_id=plans['versionId'], name=plans['name']).first()
            if rate_plan is None:
                rate_plan = RatePlan(name=plans['name'], plan_id=plans['id'], account_name=plans['accountName'],
                                     account_id=plans['accountId'],
                                     version_id=plans['versionId'], version=plans['version'], status=plans['status'],
                                     type=plans['type'], subscription_charge=plans['subscriptionCharge'],
                                     number_of_tires=plans['numberOfTiers'], tier_treatment=plans['tierTreatment'],
                                     expire_term_based_on_usage=plans['expireTermBasedOnUsage'],
                                     lengthOfTerm=plans['lengthOfTerm'],
                                     subscriptionChargeUnit=plans['subscriptionChargeUnit'], active=True)

                for tier in plans['tiers']:
                    rate_plan_tier_cost = RatePlanTierCost(tier_level=tier['tierLevel'],
                                                           subscriber_threshold=tier['subscriberThreshold'],
                                                           subscriber_capacity=tier['subscriberCapacity'],
                                                           per_subscriber_charge=tier['perSubscriberCharge'])

                    rate_plan.rate_plan_tiers.append(rate_plan_tier_cost)

                for zone in plans['zones']['reportOverageAsRoaming']:
                    rate_plan_zone = RatePlanZone(zone_name=zone,
                                                  report_overage_as_roaming=jasper_true_or_false(
                                                      plans['zones']['reportOverageAsRoaming'][
                                                          zone]))

                    rate_plan_data_usage = RatePlanDataUsage(use_default_rating=plans['dataUsage']['useDefaultRating'],
                                                             usage_limit_unit=plans['dataUsage']['usageLimitUnit'],
                                                             included_data=plans['dataUsage']['zones'][zone][
                                                                 'includedData'],
                                                             included_data_unit=plans['dataUsage']['zones'][zone][
                                                                 'includedDataUnit'],
                                                             zone_usage_limit_unit=plans['dataUsage']['zones'][zone][
                                                                 'zoneUsageLimitUnit'],
                                                             bulk_overage_enabled=plans['dataUsage']['zones'][zone][
                                                                 'bulkOverageEnabled'],
                                                             use_these_data_rounding_settings_for_all_zones=
                                                             jasper_true_or_false(
                                                                 plans['dataUsage']['zones'][zone][
                                                                     'useTheseDataRoundingSettingsForAllZones']),
                                                             data_rounding_unit=plans['dataUsage']['zones'][zone][
                                                                 'dataRoundingUnit'],
                                                             data_rounding_frequency=plans['dataUsage']['zones'][zone][
                                                                 'dataRoundingFrequency'])

                    for tier_data in plans['dataUsage']['zones'][zone]['tiers']:
                        rate_plan_tier_data_usage = RatePlanTierDataUsage(tier_level=tier_data['tierLevel'],
                                                                          subscribers_more_than=tier_data[
                                                                              'subscribersMoreThan'],
                                                                          subscribers_up_to=tier_data[
                                                                              'subscribersUpTo'],
                                                                          data_overage=tier_data['dataOverage'],
                                                                          data_overage_unit=tier_data[
                                                                              'dataOverageUnit'])

                        rate_plan_data_usage.rate_plan_tier_data_usage.append(rate_plan_tier_data_usage)
                    rate_plan_zone.rate_plan_data_usage.append(rate_plan_data_usage)

                    rate_plan_sms_usage = RatePlanSMSUsage(use_default_rating=plans['smsUsage']['useDefaultRating'],
                                                           sms_type=plans['smsUsage']['type'],
                                                           mo_and_mt_rating=plans['smsUsage']['moAndMtRating'],
                                                           pool_sms_usage=plans['smsUsage']['poolSMSUsage'],
                                                           pool_sms_mo_usage=plans['smsUsage']['poolSMSMOUsage'],
                                                           pool_sms_mt_usage=plans['smsUsage']['poolSMSMTUsage'],
                                                           included_smsmo=plans['smsUsage']['zones'][zone][
                                                               'includedSMSMO'],
                                                           included_sms_mo_unit=plans['smsUsage']['zones'][zone][
                                                               'includedSMSMOUnit'])

                    for sms_usage in plans['smsUsage']['zones'][zone]['tiers']:
                        rate_plan_tier_sms_usage = RatePlanTierSMSUsage(tier_level=sms_usage['tierLevel'],
                                                                        subscribers_more_than=sms_usage[
                                                                            'subscribersMoreThan'],
                                                                        subscribers_up_to=sms_usage['subscribersUpTo'],
                                                                        sms_overage_mo=sms_usage['smsOverageMO'],
                                                                        sms_overage_mo_unit=sms_usage[
                                                                            'smsOverageMOUnit'])

                        rate_plan_sms_usage.rate_plan_tier_sms_usages.append(rate_plan_tier_sms_usage)
                    rate_plan_zone.rate_plan_sms_usage.append(rate_plan_sms_usage)

                    rate_plan_voice_usage = RatePlanVoiceUsage(
                        use_default_rating=plans['voiceUsage']['useDefaultRating'],
                        voice_type=plans['voiceUsage']['type'],
                        mo_and_mt_rating=plans['voiceUsage']['moAndMtRating'],
                        pool_voice_usage=plans['voiceUsage']['poolVoiceUsage'],
                        pool_voice_mo_usage=plans['voiceUsage']['poolVoiceMTUsage'],
                        pool_voice_mt_usage=plans['voiceUsage']['poolVoiceMOUsage'],
                        included_voice=plans['voiceUsage']['zones'][zone]['includedVoice'],
                        included_voice_unit=plans['voiceUsage']['zones'][zone]['includedVoiceUnit'],
                        use_these_data_rounding_settings_for_all_zones=jasper_true_or_false(
                            plans['voiceUsage']['zones'][zone]['useTheseDataRoundingSettingsForAllZones']),
                        voice_rounding_unit=plans['voiceUsage']['zones'][zone]['voiceRoundingUnit'])

                    for voice_usage in plans['voiceUsage']['zones'][zone]['tiers']:
                        rate_plan_tier_voice_usage = RatePlanTierVoiceUsage(tier_level=voice_usage['tierLevel'],
                                                                            subscribers_more_than=voice_usage[
                                                                                'subscribersMoreThan'],
                                                                            subscribers_up_to=voice_usage[
                                                                                'subscribersUpTo'],
                                                                            voice_overage=voice_usage['voiceOverage'],
                                                                            voice_overage_unit=voice_usage[
                                                                                'voiceOverageUnit'])

                        rate_plan_voice_usage.rate_plan_tier_voice_usages.append(rate_plan_tier_voice_usage)
                    rate_plan_zone.rate_plan_voice_usage.append(rate_plan_voice_usage)
                rate_plan.rate_plan_zones.append(rate_plan_zone)
                db.session.add(rate_plan)
                db.session.commit()
            finish_task()


@celery.task()
def new_get_iccids(username, api_key, resource_url):
    jasper_account = JasperAccount.query.filter_by(resource_url=resource_url).first()
    for rate in RatePlan.query.all():
        list_of_imei = rest.get_usage_by_rate_plan(username, api_key, resource_url, rate.name)
        for iccid in list_of_imei:
            subscriber_identity_module = SubscriberIdentityModule.query.filter_by(iccid=iccid['iccid']).first()
            if subscriber_identity_module is None:
                jasper_account.subscriber_identity_modules.append(SubscriberIdentityModule(imei=iccid['iccid']))
    db.session.add(jasper_account)
    db.session.commit()


@celery.task()
def update_iccids(username, api_key, resource_url):
    jasper_account = JasperAccount.query.filter_by(resource_url=resource_url).first()
    for x in jasper_account.subscriber_identity_modules:
        jasper = rest.get_iccid_info(username, api_key, resource_url, x.imei)
        jasper_account.update({'imsi':jasper['imsi'], 'msisdn':jasper['msisdn'] ,'status':jasper['status']
                                  , 'communication_plan':jasper['communicationPlan']
        , 'date_activated': datetime.datetime.strptime(jasper['dateActivated'], '%Y-%m-%d %H:%M:%S.%3N%z')
        , 'date_added':jasper['dateAdded'] , 'date_updated':jasper['dateUpdated'] , 'date_shipped':jasper['dateShipped']
        , 'account_id':jasper['accountId'] , jasper['fixedIPAddress'] , jasper['operatorCustom1']
        , jasper['operatorCustom2'] , jasper['operatorCustom3'] , jasper['operatorCustom4']
        , jasper['operatorCustom5'] , jasper['accountCustom1'] , jasper['accountCustom2']
        , jasper['accountCustom3'] , jasper['accountCustom4'] , jasper['accountCustom5']
        , jasper['accountCustom6'] , jasper['accountCustom7'] , jasper['accountCustom8']
        , jasper['accountCustom9'] , jasper['accountCustom10'] , jasper['customerCustom1']
        , jasper['customerCustom2'] , jasper['customerCustom3']
        , jasper['customerCustom4'] , jasper['customerCustom5'] , jasper['simNotes']
        , jasper['euiccid'] , jasper['deviceID'] , jasper['modemID']
        , jasper['globalSimType'] , jasper['mec'] })
    db.session.commit()


#                 datetime.datetime.strptime('2019-01-26 12:01:17.068+0000', '%Y-%m-%d %H:%M:%S.%3N%z')
#  {'iccid': '89302690201004801075', 'imsi': '302690500222835', 'msisdn': '16479084795', 'imei': '3589420542722502', 'status': 'ACTIVATED', 'ratePlan': 'London Hydro Modem Share 500KB', 'communicationPlan': 'London Hydro Comm Plan 1', 'customer': 'EMD BU 80', 'endConsumerId': None, 'dateActivated': '2019-01-26 12:01:17.068+0000', 'dateAdded': '2018-01-30 21:42:21.481+0000', 'dateUpdated': '2022-03-31 17:41:35.287+0000', 'dateShipped': '2018-03-13 14:17:24.358+0000', 'accountId': '100025813', 'fixedIPAddress': '172.17.3.225', 'operatorCustom1': 'ON', 'operatorCustom2': 'London Hydro inc', 'operatorCustom3': '100025813', 'operatorCustom4': '260914', 'operatorCustom5': '0100491949', 'accountCustom1': '', 'accountCustom2': '', 'accountCustom3': '', 'accountCustom4': '', 'accountCustom5': '', 'accountCustom6': '', 'accountCustom7': '', 'accountCustom8': '', 'accountCustom9': '', 'accountCustom10': '', 'customerCustom1': '', 'customerCustom2': '', 'customerCustom3': '', 'customerCustom4': '', 'customerCustom5': '', 'simNotes': None, 'euiccid': None, 'deviceID': None, 'modemID': 'MV90-Digi{MeterNumber:701312', 'globalSimType': 'NONE', 'mec': None}
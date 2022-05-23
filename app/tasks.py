from celery import current_task
from flask import flash
from app import celery, db
from app.models import JasperAccount, JasperCredential, User, RatePlan, RatePlanZone, RatePlanTierDataUsage, \
    RatePlanSMSUsage, RatePlanTierSMSUsage, RatePlanVoiceUsage, \
    RatePlanTierVoiceUsage, RatePlanDataUsage, RatePlanTierCost, SubscriberIdentityModule
from app.jasper import rest
from datetime import datetime


def finish_task():
    job = current_task
    task = Task.query.filter_by(id=job.request.id).first()
    task.complete = True
    db.session.commit()


@celery.task()
def add_api_connections(username, api_key, resource_url, current_user_id):
    response = rest.echo(username, api_key, resource_url)
    datetime_stamp = datetime.now()
    if response[0] == "data":
        user = User.query.filter_by(id=current_user_id).first()

        jasper_credential = JasperCredential.query.filter_by(api_key=api_key, username=username).first()

        if jasper_credential is None:
            jasper_credential = JasperCredential(username=username, api_key=api_key, users=user,
                                                 last_check=datetime_stamp, last_confirmed=datetime_stamp)

        jasper_account = JasperAccount.query.filter_by(resource_url=resource_url).first()
        if jasper_account is None:
            jasper_credential.jasper_accounts.append(JasperAccount(resource_url=resource_url,
                                                                   last_check=datetime_stamp,
                                                                   last_confirmed=datetime_stamp))
        else:
            jasper_account.last_check = datetime.now()
            jasper_account.last_confirmed = datetime.now()
        db.session.add(jasper_credential)
        db.session.commit()


@celery.task()
def add_rate_plans(username, api_key, resource_url):
    response = rest.get_rate_plan(username, api_key, resource_url)
    if response[0] == "error":
        # finish_task()
        flash("rate plan download Error")
    elif response[0] == "data":
        for plans in response[1]:
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
                                                  report_overage_as_roaming=rest.jasper_true_or_false(
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
                                                             rest.jasper_true_or_false(
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
                        use_these_data_rounding_settings_for_all_zones=rest.jasper_true_or_false(
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
                jasper_account = JasperAccount.query.filter_by(resource_url=resource_url).first()
                jasper_account.rate_plans.append(rate_plan)
                db.session.commit()
            # finish_task()


#bad code
@celery.task()
def get_iccids(username, api_key, resource_url):
    jasper_account = JasperAccount.query.filter_by(resource_url=resource_url).first()
    for rate in RatePlan.query.all():
        list_of_iccid = rest.get_usage_by_rate_plan(username, api_key, resource_url, rate.name)
        if list_of_iccid[0] == "data":
            for iccid in list_of_iccid[1]:
                subscriber_identity_module = SubscriberIdentityModule.query.filter_by(iccid=iccid['iccid']).first()
                if subscriber_identity_module is None:
                    jasper_account.subscriber_identity_modules.append(SubscriberIdentityModule(iccid=iccid['iccid']))
    db.session.add(jasper_account)
    db.session.commit()


@celery.task()
def update_iccids(username, api_key, resource_url):
    jasper_account = JasperAccount.query.filter_by(resource_url=resource_url).first()
    for sim in jasper_account.subscriber_identity_modules:
        response = rest.get_iccid_info(username, api_key, resource_url, sim.iccid)
        if response[0] == "data":
            # jasper_account.update({'imei':response[1]['imei']})
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



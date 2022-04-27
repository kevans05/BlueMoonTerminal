from app import db


class AssociationBetweenSubscriberIdentityModuleDevice(db.Model):
    __tablename__ = 'association_between_subscriber_identity_module_device'
    subscriber_identity_module_id = db.Column(db.ForeignKey('subscriber_identity_module.id'), primary_key=True)
    rate_plan_id = db.Column(db.ForeignKey('rate_plan.id'), primary_key=True)
    date_time_of_change = db.Column(db.DateTime())
    rate_plans = db.relationship("RatePlan", back_populates="sims")
    sim = db.relationship("SIM", back_populates="devices")


class AssociationBetweenSubscriberIdentityModuleRatePlan(db.Model):
    __tablename__ = 'association_between_subscriber_identity_module_rate_plan'
    subscriber_identity_module_id = db.Column(db.ForeignKey('subscriber_identity_module.id'), primary_key=True)
    device_id = db.Column(db.ForeignKey('device.id'), primary_key=True)
    date_time_of_change = db.Column(db.DateTime())
    device = db.relationship("Device", back_populates="sims")
    sim = db.relationship("SIM", back_populates="devices")


class JasperAccount(db.Model):
    __tablename__ = "jasper_account"
    id = db.Column(db.Integer, primary_key=True)
    resource_url = db.Column(db.String(256))

    jasper_credentials = db.relationship("jasper_credential", back_populates="jasper_account")
    subscriber_identity_module = db.relationship("subscriber_identity_module", back_populates="jasper_account")
    rate_plans = db.relationship("rate_plan", back_populates="jasper_account")


class JasperCredential(db.Model):
    __tablename__ = "jasper_credential"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256))
    api_key = db.Column(db.String(256))

    jasper_account_id = db.Column(db.Integer, db.ForeignKey('jasper_account.id'))
    jasper_account = db.relationship("jasper_account", back_populates="jasper_credentials")


class RatePlan(db.Model):
    __tablename__ = "rate_plan"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    plan_id = db.Column(db.Integer)
    account_name = db.Column(db.String(256))
    account_id = db.Column(db.String(256))
    version_id = db.Column(db.Integer)
    version = db.Column(db.Integer)
    status = db.Column(db.String(256))
    type = db.Column(db.String(256))
    subscription_charge = db.Column(db.Integer)
    number_of_tires = db.Column(db.Integer)
    tier_treatment = db.Column(db.String(256))
    expire_term_based_on_usage = db.Column(db.Boolean)
    lengthOfTerm = db.Column(db.Integer)
    subscriptionChargeUnit = db.Column(db.String(256))
    active = db.Column(db.Boolean)

    sims = db.relationship("AssociationBetweenSubscriberIdentityModuleRatePlan", back_populates="rate_plans")

    jasper_account_id = db.Column(db.Integer, db.ForeignKey('jasper_account.id'))
    jasper_account = db.relationship("jasper_account", back_populates="rate_plans")

    rate_plan_tiers = db.relationship("rate_plan_tier", back_populates="parent")
    rate_plan_zones = db.relationship("rate_plan_zone", back_populates="parent")


class RatePlanTierCost(db.Model):
    __tablename__ = "rate_plan_tier"
    id = db.Column(db.Integer, primary_key=True)
    tier_level = db.Column(db.Integer)
    subscriber_threshold = db.Column(db.Integer)
    subscriber_capacity = db.Column(db.String(256))
    per_subscriber_charge = db.Column(db.Integer)

    rate_plan_id = db.Column(db.Integer, db.ForeignKey('rate_plan.id'))
    rate_plan = db.relationship("RatePlan", back_populates="rate_plan_tiers")


class RatePlanZone(db.Model):
    __tablename__ = "rate_plan_zone"
    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(256))
    report_overage_as_roaming = db.Column(db.Boolean)

    rate_plan_data_usage = db.relationship("RatePlanDataUsage", back_populates="rate_plan_zone")
    rate_plan_sms_usage = db.relationship("RatePlanSMSUsage", back_populates="rate_plan_zone")
    rate_plan_voice_usage = db.relationship("RatePlanVoiceUsage", back_populates="rate_plan_zone")

    rate_plan_id = db.Column(db.Integer, db.ForeignKey('rate_plan.id'))
    rate_plan = db.relationship("RatePlan", back_populates="rate_plan_tiers")


class RatePlanDataUsage(db.Model):
    __tablename__ = "rate_plan_data_usage"
    id = db.Column(db.Integer, primary_key=True)

    use_default_rating = db.Column(db.Boolean)
    usage_limit_unit = db.Column(db.String(256))

    included_data = db.Column(db.BIGINT)
    included_data_unit = db.Column(db.String(2))
    zone_usage_limit_unit = db.Column(db.String(256))
    bulk_overage_enabled = db.Column(db.Boolean)
    use_these_data_rounding_settings_for_all_zones = db.Column(db.Boolean)
    data_rounding_unit = db.Column(db.String(256))
    data_rounding_frequency = db.Column(db.String(256))

    rate_plan_tier_data_usage = db.relationship("RatePlanTierDataUsage", back_populates="rate_plan_data_usage")

    rate_plan_zone_id = db.Column(db.Integer, db.ForeignKey('rate_plan_zone.id'))
    rate_plan_zone = db.relationship("RatePlanDataUsage", back_populates="rate_plan_data_usage")


class RatePlanTierDataUsage(db.Model):
    __tablename__ = "rate_plan_tier_data_usage"
    id = db.Column(db.Integer, primary_key=True)

    tier_level = db.Column(db.Integer)
    subscribers_more_than = db.Column(db.Integer)
    subscribers_up_to = db.Column(db.String(256))
    data_overage = db.Column(db.Float)
    data_overage_unit = db.Column(db.String(256))

    rate_plan_data_usage_id = db.Column(db.Integer, db.ForeignKey('rate_plan_data_usage.id'))
    rate_plan_data_usage = db.relationship("RatePlanTierDataUsage", back_populates="rate_plan_tier_data_usage")


class RatePlanSMSUsage(db.Model):
    __tablename__ = "rate_plan_sms_usage"
    id = db.Column(db.Integer, primary_key=True)

    use_default_rating = db.Column(db.Boolean)
    sms_type = db.Column(db.String(256))
    mo_and_mt_rating = db.Column(db.String(256))
    pool_sms_usage = db.Column(db.Boolean)
    pool_sms_mo_usage = db.Column(db.Boolean)
    pool_sms_mt_usage = db.Column(db.Boolean)
    included_smsmo = db.Column(db.Boolean)
    included_sms_mo_unit = db.Column(db.Boolean)

    rate_plan_tier_sms_usage = db.relationship("RatePlanTierSMSUsage", back_populates="rate_plan_tier_sms_usage")

    rate_plan_zone_id = db.Column(db.Integer, db.ForeignKey('rate_plan_zone.id'))
    rate_plan_zone = db.relationship("RatePlanSMSUsage", back_populates="rate_plan_sms_usage")


class RatePlanTierSMSUsage(db.Model):
    __tablename__ = "rate_plan_tier_sms_usage"
    id = db.Column(db.Integer, primary_key=True)

    tier_level = db.Column(db.Integer)
    subscribers_more_than = db.Column(db.Integer)
    subscribers_up_to = db.Column(db.String(256))
    sms_overage_mo = db.Column(db.Float)
    sms_overage_mo_unit = db.Column(db.String(256))

    rate_plan_sms_usage_id = db.Column(db.Integer, db.ForeignKey('rate_plan_sms_usage.id'))
    rate_plan_sms_usage = db.relationship("RatePlanSMSUsage", back_populates="rate_plan_tier_sms_usage")


class RatePlanVoiceUsage(db.Model):
    __tablename__ = "rate_plan_voice_usage"
    id = db.Column(db.Integer, primary_key=True)

    use_default_rating = db.Column(db.Boolean)
    voice_type = db.Column(db.String(256))
    mo_and_mt_rating = db.Column(db.String(256))
    pool_voice_usage = db.Column(db.Boolean)
    pool_voice_mo_usage = db.Column(db.Boolean)
    pool_voice_mt_usage = db.Column(db.Boolean)
    included_voice = db.Column(db.String(256))
    included_voice_unit = db.Column(db.String(256))
    use_these_data_rounding_settings_for_all_zones = db.Column(db.Boolean)
    voice_rounding_unit = db.Column(db.String(256))

    rate_plan_tier_voice_usage = db.relationship("RatePlanTierVoiceUsage", back_populates="rate_plan_tier_voice_usage")

    rate_plan_zone_id = db.Column(db.Integer, db.ForeignKey('rate_plan_zone.id'))
    rate_plan_zone = db.relationship("RatePlanVoiceUsage", back_populates="rate_plan_voice_usage")


class RatePlanTierVoiceUsage(db.Model):
    __tablename__ = "rate_plan_tier_voice_usage"
    id = db.Column(db.Integer, primary_key=True)

    tier_level = db.Column(db.Integer)
    subscribers_more_than = db.Column(db.Integer)
    subscribers_up_to = db.Column(db.String(256))
    voice_overage = db.Column(db.Integer)
    voice_overage_unit = db.Column(db.String(256))

    rate_plan_voice_usage_id = db.Column(db.Integer, db.ForeignKey('rate_plan_voice_usage.id'))
    rate_plan_voice_usage = db.relationship("RatePlanTierVoiceUsage", back_populates="rate_plan_tier_voice_usage")


class SubscriberIdentityModule(db.Model):
    __tablename__ = "subscriber_identity_module"
    id = db.Column(db.Integer, primary_key=True)
    imei = db.Column(db.String(256))
    imsi = db.Column(db.String(256))
    msisdn = db.Column(db.String(256))
    status = db.Column(db.String(256))
    communication_plan = db.Column(db.String(256))

    date_activated = db.Column(db.DateTime())
    date_added = db.Column(db.DateTime())
    date_updated = db.Column(db.DateTime())
    date_shipped = db.Column(db.DateTime())
    account_id = db.Column(db.String(256))
    operator_custom1 = db.Column(db.String(256))
    operator_custom2 = db.Column(db.String(256))
    operator_custom3 = db.Column(db.String(256))
    operator_custom4 = db.Column(db.String(256))
    account_custom1 = db.Column(db.String(256))
    account_custom2 = db.Column(db.String(256))
    account_custom3 = db.Column(db.String(256))
    account_custom4 = db.Column(db.String(256))
    account_custom5 = db.Column(db.String(256))
    account_custom6 = db.Column(db.String(256))
    account_custom7 = db.Column(db.String(256))
    account_custom8 = db.Column(db.String(256))
    account_custom9 = db.Column(db.String(256))
    account_custom10 = db.Column(db.String(256))
    customer_custom1 = db.Column(db.String(256))
    customer_custom2 = db.Column(db.String(256))
    customer_custom3 = db.Column(db.String(256))
    customer_custom4 = db.Column(db.String(256))
    customer_custom5 = db.Column(db.String(256))
    sim_notes = db.Column(db.String(256))
    euiccid = db.Column(db.String(256))
    device_id = db.Column(db.String(256))
    modem_id = db.Column(db.String(256))
    global_sim_type = db.Column(db.String(256))
    mec = db.Column(db.String(256))

    devices = db.relationship("AssociationBetweenSubscriberIdentityModuleDevice", back_populates="sim")
    data_usage_to_date = db.relationship("DataUsageToDate", back_populates="subscriber_identity_module")
    rate_plans = db.relationship("AssociationBetweenSubscriberIdentityModuleRatePlan", back_populates="sim")


class Device(db.Model):
    __tablename__ = "device"
    id = db.Column(db.Integer, primary_key=True)
    imei = db.Column(db.String(256))
    serial_number = db.Column(db.String(256))
    manufacture = db.Column(db.String(256))
    device_name = db.Column(db.String(256))
    sims = db.relationship("AssociationBetweenSubscriberIdentityModuleDevice", back_populates="device")


class DataUsageToDate(db.Model):
    __tablename__ = "data_usage_to_date"
    id = db.Column(db.Integer, primary_key=True)
    ctdDataUsage = db.Column(db.BIGINT)
    ctdSMSUsage = db.Column(db.BIGINT)
    ctdVoiceUsage = db.Column(db.BIGINT)
    date_updated = db.Column(db.DateTime())

    sim_id = db.Column(db.Integer, db.ForeignKey('subscriber_identity_module.id'))
    sim = db.relationship("SubscriberIdentityModule", back_populates="DataUsageToDate")

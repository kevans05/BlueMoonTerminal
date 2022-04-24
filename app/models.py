from datetime import datetime
from hashlib import md5
from time import time

from app import db


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

    rate_plan_zone_id = db.Column(db.Integer, db.ForeignKey('rate_plan_zone.id'))
    rate_plan_zone = db.relationship("RatePlanDataUsage", back_populates="rate_plan_data_usage")


class RatePlanSMSUsage(db.Model):
    __tablename__ = "rate_plan_sms_usage"
    id = db.Column(db.Integer, primary_key=True)

    use_default_rating = db.Column(db.Boolean)

    rate_plan_zone_id = db.Column(db.Integer, db.ForeignKey('rate_plan_zone.id'))
    rate_plan_zone = db.relationship("RatePlanSMSUsage", back_populates="rate_plan_sms_usage")


class RatePlanVoiceUsage(db.Model):
    __tablename__ = "rate_plan_voice_usage"
    id = db.Column(db.Integer, primary_key=True)

    use_default_rating = db.Column(db.Boolean)

    rate_plan_zone_id = db.Column(db.Integer, db.ForeignKey('rate_plan_zone.id'))
    rate_plan_zone = db.relationship("RatePlanVoiceUsage", back_populates="rate_plan_voice_usage")


class DataUsageToDate(db.Model):
    __tablename__ = "DataUsageToDate"
    id = db.Column(db.Integer, primary_key=True)
    ctdDataUsage = db.Column(db.BIGINT)
    ctdSMSUsage = db.Column(db.BIGINT)
    ctdVoiceUsage = db.Column(db.BIGINT)


# class SubscriberIdentityModule(db.Model):
#     __tablename__ = "subscriber_identity_module"
#     id = db.Column(db.Integer, primary_key=True)
#     iccid = db.Column(db.String(256))
#     imsi = db.Column(db.String(256))
#     msidn = db.Column(db.String(256))
#
#     status = db.Column(db.String(256))
#     active = db.Column(db.Boolean)
#
#     jasper_account_id = db.Column(db.Integer, db.ForeignKey('JasperAccount.id'))
#     jasper_account = db.relationship("JasperAccount", back_populates="SubscriberIdentityModule")
#
#     mobile_equipment = db.relationship(
#         'MobileEquipment',
#         secondary='subscriber_identity_module_mobile_equipment_association_table'
#     )
#
#
# class MobileEquipment(db.Model):
#     __tablename__ = "mobile_equipment"
#     id = db.Column(db.Integer, primary_key=True)
#     imei = db.Column(db.String(256))
#     serial_number = db.Column(db.String(256))
#     manufacture = db.Column(db.String(256))
#     device_name = db.Column(db.String(256))
#
#     subscriber_identity_modules = db.relationship(
#         SubscriberIdentityModule,
#         secondary='SubscriberIdentityModuleMobileEquipmentAssociationTable'
#     )
#
# class SubscriberIdentityModuleMobileEquipmentAssociationTable(db.Model):
#     __tablename__ = 'subscriber_identity_module_mobile_equipment_association_table'
#     id = db.Column(db.Integer, primary_key=True, unique=True)
#     subscriber_identity_module_id = db.Column(db.Integer, db.ForeignKey('department.id'), primary_key=True)
#     mobile_equipment_id = db.Column(db.Integer, db.ForeignKey('employee.id'), primary_key=True)
#     update_date = db.Column(db.DateTime)
#     subscriber_identity_module = db.relationship(SubscriberIdentityModule, backref=db.backref("mobile_equipment_assoc"))
#     mobile_equipment = db.relationship(MobileEquipment, backref=db.backref("subscriber_identity_module_assoc"))

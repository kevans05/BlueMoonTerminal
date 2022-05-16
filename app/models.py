from time import time

import jwt
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login

association_between_jasper_credential_jasper_account = db.Table('association_between_jasper_credential_jasper_account',
                                                                db.Model.metadata, db.Column('jasper_credential_id',
                                                                                             db.ForeignKey(
                                                                                                 'jasper_credential.id')),
                                                                db.Column('jasper_account_id',
                                                                          db.ForeignKey('jasper_account.id')))


class AssociationBetweenSubscriberIdentityModuleRatePlan(db.Model):
    __tablename__ = 'association_between_subscriber_identity_module_rate_plan'
    subscriber_identity_module_id = db.Column(db.ForeignKey('subscriber_identity_module.id'), primary_key=True)
    rate_plan_id = db.Column(db.ForeignKey('rate_plan.id'), primary_key=True)
    date_time_of_change = db.Column(db.DateTime())
    rate_plans = db.relationship("RatePlan",
                                 backref=db.backref("association_between_subscriber_identity_module_rate_plan",
                                                    cascade="all, delete-orphan"))
    sim = db.relationship("SubscriberIdentityModule",
                          backref=db.backref("association_between_subscriber_identity_module_rate_plan",
                                             cascade="all, delete-orphan"))


class AssociationBetweenSubscriberIdentityModuleDevice(db.Model):
    __tablename__ = 'association_between_subscriber_identity_module_device'
    subscriber_identity_module_id = db.Column(db.ForeignKey('subscriber_identity_module.id'), primary_key=True)
    device_id = db.Column(db.ForeignKey('device.id'), primary_key=True)
    date_time_of_change = db.Column(db.DateTime())
    device = db.relationship("Device", backref=db.backref("association_between_subscriber_identity_module_device",
                                                          cascade="all, delete-orphan"))
    sim = db.relationship("SubscriberIdentityModule",
                          backref=db.backref("association_between_subscriber_identity_module_device",
                                             cascade="all, delete-orphan"))


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    # jasper_credential_id = db.Column(db.Integer, db.ForeignKey('jasper_credential.id'))
    # jasper_credential = db.relationship("jasper_credential", back_populates="user")

    jasper_credential = db.relationship("JasperCredential", back_populates="users")

    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class JasperAccount(db.Model):
    __tablename__ = "jasper_account"
    id = db.Column(db.Integer, primary_key=True)
    resource_url = db.Column(db.String(256))
    cell_provider = db.Column(db.String(256))

    subscriber_identity_modules = db.relationship("SubscriberIdentityModule", back_populates="jasper_accounts")

    rate_plans = db.relationship("RatePlan", back_populates="jasper_account")

    jasper_credentials = db.relationship("JasperCredential",
                                         secondary=association_between_jasper_credential_jasper_account,
                                         back_populates="jasper_accounts")

    # jasper_credentials = db.relationship("jasper_credential", back_populates="jasper_account")


class JasperCredential(db.Model):
    __tablename__ = "jasper_credential"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256))
    api_key = db.Column(db.String(256))

    jasper_accounts = db.relationship("JasperAccount", secondary=association_between_jasper_credential_jasper_account,
                                      back_populates="jasper_credentials")

    users_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    users = db.relationship("User", back_populates="jasper_credential")

    # jasper_account_id = db.Column(db.Integer, db.ForeignKey('jasper_account.id'))
    # jasper_account = db.relationship("jasper_account", back_populates="jasper_credentials")
    # users = db.relationship("user", back_populates="jasper_credential")


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
    jasper_account = db.relationship("JasperAccount", back_populates="rate_plans")

    rate_plan_tiers = db.relationship("RatePlanTierCost", back_populates="rate_plan")
    rate_plan_zones = db.relationship("RatePlanZone", back_populates="rate_plan")


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

    rate_plan_data_usage = db.relationship("RatePlanDataUsage", back_populates="rate_plan_zones")
    rate_plan_sms_usage = db.relationship("RatePlanSMSUsage", back_populates="rate_plan_zones")
    rate_plan_voice_usage = db.relationship("RatePlanVoiceUsage", back_populates="rate_plan_zones")

    rate_plan_id = db.Column(db.Integer, db.ForeignKey('rate_plan.id'))
    rate_plan = db.relationship("RatePlan", back_populates="rate_plan_zones")


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

    rate_plan_tier_data_usage = db.relationship("RatePlanTierDataUsage", back_populates="rate_plan_data_usages")

    rate_plan_zone_id = db.Column(db.Integer, db.ForeignKey('rate_plan_zone.id'))
    rate_plan_zones = db.relationship("RatePlanZone", back_populates="rate_plan_data_usage")


class RatePlanTierDataUsage(db.Model):
    __tablename__ = "rate_plan_tier_data_usage"
    id = db.Column(db.Integer, primary_key=True)

    tier_level = db.Column(db.Integer)
    subscribers_more_than = db.Column(db.Integer)
    subscribers_up_to = db.Column(db.String(256))
    data_overage = db.Column(db.Float)
    data_overage_unit = db.Column(db.String(256))

    rate_plan_data_usages_id = db.Column(db.Integer, db.ForeignKey('rate_plan_data_usage.id'))
    rate_plan_data_usages = db.relationship("RatePlanDataUsage", back_populates="rate_plan_tier_data_usage")


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

    rate_plan_tier_sms_usages = db.relationship("RatePlanTierSMSUsage", back_populates="rate_plan_sms_usages")

    rate_plan_zones_id = db.Column(db.Integer, db.ForeignKey('rate_plan_zone.id'))
    rate_plan_zones = db.relationship("RatePlanZone", back_populates="rate_plan_sms_usage")


class RatePlanTierSMSUsage(db.Model):
    __tablename__ = "rate_plan_tier_sms_usage"
    id = db.Column(db.Integer, primary_key=True)

    tier_level = db.Column(db.Integer)
    subscribers_more_than = db.Column(db.Integer)
    subscribers_up_to = db.Column(db.String(256))
    sms_overage_mo = db.Column(db.Float)
    sms_overage_mo_unit = db.Column(db.String(256))

    rate_plan_sms_usages_id = db.Column(db.Integer, db.ForeignKey('rate_plan_sms_usage.id'))
    rate_plan_sms_usages = db.relationship("RatePlanSMSUsage", back_populates="rate_plan_tier_sms_usages")


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

    rate_plan_tier_voice_usages = db.relationship("RatePlanTierVoiceUsage", back_populates="rate_plan_voice_usages")

    rate_plan_zones_id = db.Column(db.Integer, db.ForeignKey('rate_plan_zone.id'))
    rate_plan_zones = db.relationship("RatePlanZone", back_populates="rate_plan_voice_usage")


class RatePlanTierVoiceUsage(db.Model):
    __tablename__ = "rate_plan_tier_voice_usage"
    id = db.Column(db.Integer, primary_key=True)

    tier_level = db.Column(db.Integer)
    subscribers_more_than = db.Column(db.Integer)
    subscribers_up_to = db.Column(db.String(256))
    voice_overage = db.Column(db.Integer)
    voice_overage_unit = db.Column(db.String(256))

    rate_plan_voice_usages_id = db.Column(db.Integer, db.ForeignKey('rate_plan_voice_usage.id'))
    rate_plan_voice_usages = db.relationship("RatePlanVoiceUsage", back_populates="rate_plan_tier_voice_usages")


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

    devices = db.relationship("AssociationBetweenSubscriberIdentityModuleRatePlan", back_populates="sim")
    data_usage_to_date = db.relationship("DataUsageToDate", back_populates="sim")
    rate_plans = db.relationship("AssociationBetweenSubscriberIdentityModuleRatePlan", back_populates="sim")

    jasper_account_id = db.Column(db.Integer, db.ForeignKey('jasper_account.id'))
    jasper_accounts = db.relationship("JasperAccount", back_populates="subscriber_identity_modules")


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
    sim = db.relationship("SubscriberIdentityModule", back_populates="data_usage_to_date")


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    complete = db.Column(db.Boolean, default=False)

    users_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    users = db.relationship("User", back_populates="tasks")

    # def get_rq_job(self):
    #     try:
    #         rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
    #     except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
    #         return None
    #     return rq_job
    #
    # def get_progress(self):
    #     job = self.get_rq_job()
    #     return job.meta.get('progress', 0) if job is not None else 100
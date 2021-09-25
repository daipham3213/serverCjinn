sql_apps = {'apps.account', 'apps.auths', 'apps.base', 'apps.logs'}
default_apps = {'admin', 'session'}


class DBRouter:
    route_app_labels = {**sql_apps, **default_apps}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (obj1._meta.app_label in self.route_app_labels or obj2._meta in self.route_app_labels):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return 'default'
        return None


class NOSQLRouter:
    def db_for_read(self, model, **hints):
        # Specify target database with field in_db in model's Meta class
        if hasattr(model._meta, 'in_db') and model._meta.app_label not in sql_apps:
            return model._meta.in_db
        return None

    def db_for_write(self, model, **hints):
        # Specify target database with field in_db in model's Meta class
        if hasattr(model._meta, 'in_db') and model._meta.app_label not in sql_apps:
            return model._meta.in_db
        return None

    def allow_migrate(self, db, model):
        # Specify target database with field in_db in model's Meta class
        if hasattr(model._meta, 'in_db'):
            if model._meta.in_db == db:
                return True
            else:
                return False
        else:
            # Random models that don't specify a database can only go to 'default'
            if db == 'default':
                return True
            else:
                return False

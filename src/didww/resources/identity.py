from didww.resources.base import BaseResource, Repository


class Identity(BaseResource):
    _type = "identities"
    _writable_attrs = {"first_name", "last_name", "phone_number", "id_number", "birth_date",
                       "company_name", "company_reg_number", "vat_id", "description",
                       "personal_tax_id", "identity_type", "external_reference_id", "contact_email"}

    @property
    def first_name(self):
        return self._attr("first_name")

    @first_name.setter
    def first_name(self, value):
        self._set_attr("first_name", value)

    @property
    def last_name(self):
        return self._attr("last_name")

    @last_name.setter
    def last_name(self, value):
        self._set_attr("last_name", value)

    @property
    def phone_number(self):
        return self._attr("phone_number")

    @phone_number.setter
    def phone_number(self, value):
        self._set_attr("phone_number", value)

    @property
    def id_number(self):
        return self._attr("id_number")

    @id_number.setter
    def id_number(self, value):
        self._set_attr("id_number", value)

    @property
    def birth_date(self):
        return self._attr("birth_date")

    @birth_date.setter
    def birth_date(self, value):
        self._set_attr("birth_date", value)

    @property
    def company_name(self):
        return self._attr("company_name")

    @company_name.setter
    def company_name(self, value):
        self._set_attr("company_name", value)

    @property
    def company_reg_number(self):
        return self._attr("company_reg_number")

    @company_reg_number.setter
    def company_reg_number(self, value):
        self._set_attr("company_reg_number", value)

    @property
    def vat_id(self):
        return self._attr("vat_id")

    @vat_id.setter
    def vat_id(self, value):
        self._set_attr("vat_id", value)

    @property
    def description(self):
        return self._attr("description")

    @description.setter
    def description(self, value):
        self._set_attr("description", value)

    @property
    def personal_tax_id(self):
        return self._attr("personal_tax_id")

    @personal_tax_id.setter
    def personal_tax_id(self, value):
        self._set_attr("personal_tax_id", value)

    @property
    def identity_type(self):
        return self._attr("identity_type")

    @identity_type.setter
    def identity_type(self, value):
        self._set_attr("identity_type", value)

    @property
    def contact_email(self):
        return self._attr("contact_email")

    @contact_email.setter
    def contact_email(self, value):
        self._set_attr("contact_email", value)

    @property
    def external_reference_id(self):
        return self._attr("external_reference_id")

    @external_reference_id.setter
    def external_reference_id(self, value):
        self._set_attr("external_reference_id", value)

    @property
    def created_at(self):
        return self._attr("created_at")

    @property
    def verified(self):
        return self._attr("verified")

    def set_country(self, country_id):
        self._set_relationship("country", "countries", country_id)


class IdentityRepository(Repository):
    _resource_class = Identity
    _path = "identities"

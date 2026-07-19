import {
  Check,
  CheckGroup,
  Field,
  FormPage,
  PageGate,
  Paragraph,
  Row,
  Section,
  TextArea,
  YesNoCheck,
} from './form-ui'

/** From https://github.com/hai1975/form-builder-pro adult-en — wired to VMC3 field ids */
export function AdultEnForm() {
  return (
    <FormPage title="NEW PATIENT REGISTRATION FORM">
      <PageGate page={1}>
        <Field label="Patient Name" name="patient_name" />
        <Row>
          <Field label="Birthday" name="birthday" type="date" />
          <Field label="SSN" name="ssn" />
        </Row>
        <TextArea label="Home address" name="home_address" />
        <Row>
          <Field label="Phone" name="phone" />
          <Field label="Email" name="email" type="email" />
        </Row>

        <CheckGroup
          title="Insurance"
          name="insurance"
          items={[
            { label: 'Medi-Cal', value: 'medi_cal' },
            { label: 'PPO', value: 'ppo' },
            { label: 'HMO', value: 'hmo' },
            { label: 'Uninsured', value: 'uninsured' },
          ]}
        />
        <CheckGroup
          title="Race"
          name="race"
          multi
          items={[
            { label: 'Asian', value: 'asian' },
            { label: 'White', value: 'white' },
            { label: 'African American', value: 'african_american' },
            { label: 'American Indian or Alaska Native', value: 'native_american' },
            { label: 'Native Hawaiian or Other Pacific Islander', value: 'pacific_islander' },
            { label: 'Other', value: 'other' },
          ]}
        />
        <Field label="Other race, please specify" name="race_other_specify" />
        <CheckGroup
          title="Ethnicity"
          name="ethnicity"
          items={[
            { label: 'Hispanic or Latino', value: 'hispanic' },
            { label: 'Not Hispanic or Latino', value: 'not_hispanic' },
            { label: 'Unknown', value: 'unknown' },
          ]}
        />

        <CheckGroup
          title="Gender Identity"
          name="gender_identity"
          items={[
            { label: 'Male', value: 'male' },
            { label: 'Female', value: 'female' },
            { label: 'Choose not to disclose', value: 'not_disclose' },
            { label: 'Female-to-Male (FTM) / Transgender Male', value: 'ftm' },
            { label: 'Male-to-Female (MTF) / Transgender Female', value: 'mtf' },
            { label: 'Genderqueer, neither exclusively male nor female', value: 'genderqueer' },
            { label: 'Other', value: 'other' },
          ]}
        />

        <CheckGroup
          title="Sexual Orientation"
          name="sexual_orientation"
          items={[
            { label: 'Lesbian, gay, or homosexual', value: 'gay_lesbian' },
            { label: 'Straight or heterosexual', value: 'straight' },
            { label: 'Bisexual', value: 'bisexual' },
            { label: 'Do not know', value: 'unknown' },
            { label: 'Choose to not disclose', value: 'not_disclose' },
            { label: 'Other', value: 'other' },
          ]}
        />

        <Row>
          <Field label="Preferred Pharmacy Name" name="pharmacy_name" />
          <Field label="Pharmacy Phone" name="pharmacy_phone" />
        </Row>

        <Section title="TREATMENT CONSENT">
          <Paragraph>
            I hereby authorize VM Clinic, its physicians, nurse practitioners, physician assistants, and other healthcare
            professionals to evaluate and treat me for my medical condition(s). I understand this may include physical
            examinations, diagnostic tests, medical treatments, and other procedures deemed necessary for my care. All
            procedures and treatments will be explained to me including risks and benefits. I have the right to ask
            questions, refuse or withdraw consent at any time. I am financially responsible for all services rendered,
            including those not covered by insurance, and certify that the insurance information provided is factual and
            correct.
          </Paragraph>
          <Check label="I agree / Treatment Consent" name="treatment_consent" />
        </Section>
      </PageGate>

      <PageGate page={2}>
        <Section title="MEDICAL HISTORY">
          <Row>
            <Field label="Patient's Name" name="medical_history_patient_name" />
            <Field label="DOB" name="medical_history_dob" type="date" />
          </Row>
          <div>
            <p className="font-medium mb-1">Have you ever had or been diagnosed with any of the following?</p>
            <div className="flex flex-wrap gap-y-2">
              <Check label="Diabetes" name="med_cond_diabetes" />
              <Check label="High Blood Pressure" name="med_cond_high_blood_pressure" />
              <Check label="High Cholesterol" name="med_cond_high_cholesterol" />
              <Check label="Heart Disease" name="med_cond_heart_disease" />
              <Check label="Asthma" name="med_cond_asthma" />
              <Check label="Stroke" name="med_cond_stroke" />
              <Check label="Kidney Disease" name="med_cond_kidney_disease" />
              <Check label="Liver Disease" name="med_cond_liver_disease" />
              <Check label="Seizures" name="med_cond_seizures" />
              <Check label="Cancer" name="med_cond_cancer" />
              <Check label="Mental Health Conditions (e.g., depression, anxiety)" name="med_cond_mental_health" />
            </div>
          </div>
          <Field label="Cancer type" name="cancer_type" />
          <Field label="Other conditions" name="other_medical_conditions" />
          <TextArea label="Please list any surgeries and the year they occurred" name="surgeries" />
          <TextArea
            label="Please list all current medications (prescription, OTC, supplements)"
            name="current_medications"
            rows={3}
          />
          <YesNoCheck title="Hospitalized within the past 6 months?" name="hospitalized_6_months" />
          <TextArea label="If yes, please specify" name="hospitalized_details" />
          <div>
            <p className="font-medium mb-1">Allergies</p>
            <div className="flex flex-wrap gap-y-2">
              <Check label="No known allergies" name="no_known_allergies" />
            </div>
          </div>
          <Field label="Medication allergies" name="medication_allergies" />
          <Field label="Food allergies" name="food_allergies" />
          <Field label="Environmental allergies" name="environmental_allergies" />
        </Section>
      </PageGate>

      <PageGate page={3}>
        <Section title="FAMILY HISTORY & LIFESTYLE">
          <CheckGroup
            title="Family history"
            name="family_history"
            multi
            items={[
              { label: 'Diabetes', value: 'diabetes' },
              { label: 'Cancer', value: 'cancer' },
              { label: 'Heart Disease', value: 'heart_disease' },
              { label: 'High Blood Pressure', value: 'high_blood_pressure' },
              { label: 'Stroke', value: 'stroke' },
              { label: 'Mental Illness', value: 'mental_illness' },
              { label: 'Other', value: 'other' },
            ]}
          />
          <Field label="Family history (other)" name="family_history_other" />
          <YesNoCheck title="Exposed to secondhand smoke?" name="secondhand_smoke" />
          <YesNoCheck title="Do you smoke/use tobacco?" name="tobacco_use" />
          <Field label="Tobacco (how much/often)" name="tobacco_frequency" />
          <YesNoCheck title="Alcohol?" name="alcohol_use" />
          <Field label="Alcohol (how much/often)" name="alcohol_frequency" />
          <YesNoCheck title="Recreational drugs?" name="recreational_drugs" />
          <Field label="Recreational drugs (list)" name="recreational_drugs_list" />
          <YesNoCheck title="Do you feel safe where you live?" name="feel_safe_home" />
          <CheckGroup
            title="Vaccinations up to date?"
            name="vaccinations_up_to_date"
            items={[
              { label: 'Yes', value: 'yes' },
              { label: 'No', value: 'no' },
              { label: 'Unsure', value: 'unsure' },
            ]}
          />
          <CheckGroup
            title="Tested for Tuberculosis?"
            name="tb_tested"
            items={[
              { label: 'Yes', value: 'yes' },
              { label: 'No', value: 'no' },
              { label: 'Unsure', value: 'unsure' },
            ]}
          />
          <CheckGroup
            title="If yes, result?"
            name="tb_result"
            items={[
              { label: 'Negative', value: 'negative' },
              { label: 'Positive', value: 'positive' },
              { label: 'Unsure', value: 'unsure' },
            ]}
          />
          <YesNoCheck title="Specific communication requirements?" name="communication_requirements" />
          <Field label="If yes, please specify" name="communication_details" />
          <YesNoCheck title="Interpretation needed?" name="interpretation_needed" />
          <Field label="If yes, in which language?" name="interpretation_language" />
        </Section>

        <Section title="NOTICE OF PRIVACY PRACTICES ACKNOWLEDGEMENT">
          <Paragraph>
            I understand that under HIPAA (1994) I have certain rights to privacy regarding my protected health
            information. By signing this form, I acknowledge that I received the Notice of Privacy Practices of VM Clinic.
            Copies are available at www.vmclinic.us.
          </Paragraph>
          <Check label="I acknowledge" name="hipaa_acknowledgement" />
        </Section>

        <Section title="RELEASE OF INFORMATION">
          <Row>
            <Field label="Name" name="release_contact_1_name" />
            <Field label="Relationship" name="release_contact_1_relationship" />
          </Row>
          <Row>
            <Field label="Phone" name="release_contact_1_phone" />
            <YesNoCheck title="Emergency Contact" name="release_contact_1_emergency" />
          </Row>
          <Row>
            <Field label="Name" name="release_contact_2_name" />
            <Field label="Relationship" name="release_contact_2_relationship" />
          </Row>
          <Row>
            <Field label="Phone" name="release_contact_2_phone" />
            <YesNoCheck title="Emergency Contact" name="release_contact_2_emergency" />
          </Row>
        </Section>

        <Section title="ELECTRONIC COMMUNICATION CONSENT">
          <Paragraph>
            I consent to VM Clinic providing services and communicating with me via mobile phone, text messages, email,
            and other forms of online communication, provided these communications comply with applicable privacy
            regulations.
          </Paragraph>
          <Check label="I consent" name="electronic_communication_consent" />
          <Field label="Patient Name (or Legal representative)" name="consent_signer_name" />
        </Section>
      </PageGate>

      <PageGate page={4}>
        <Section title="AUTHORIZATION FOR RELEASE OF INFORMATION">
          <Row>
            <Field label="Patient Name" name="authorization_patient_name" />
            <Field label="DOB" name="authorization_dob" type="date" />
          </Row>
          <Field label="I authorize" name="release_authorization_name" />
          <Paragraph>
            Records are released to VM Medical Group as printed on this form. You do not need to name another hospital
            or provider facility.
          </Paragraph>
          <CheckGroup
            title="Information to be released"
            name="records_to_release"
            multi
            items={[
              { label: 'Complete Medical Record', value: 'complete_record' },
              { label: 'Office Visit Notes', value: 'office_notes' },
              { label: 'Lab/Pathology Reports', value: 'lab_reports' },
              { label: 'Radiology/Imaging Reports', value: 'radiology' },
              { label: 'Immunization Records', value: 'immunization' },
              { label: 'Medication Records', value: 'medication_records' },
              { label: 'Other', value: 'other' },
            ]}
          />
          <CheckGroup
            title="Purpose of Disclosure"
            name="disclosure_purpose"
            multi
            items={[
              { label: 'Continuation of care', value: 'continuation_of_care' },
              { label: 'Personal use', value: 'personal_use' },
              { label: 'Legal purposes', value: 'legal' },
              { label: 'Insurance', value: 'insurance' },
              { label: 'Post ER/Hospital F/U', value: 'post_hospital' },
              { label: 'Other', value: 'other' },
            ]}
          />
          <Paragraph>
            The purpose of this released information is continuity of care. Exchange of information ensures continuity
            of care between providers, and without such exchange my healthcare may be compromised. I understand
            specific references may be made to psychiatric conditions, HIV testing and results, and any related
            diagnosis and medical condition(s) which may be recorded in my health records. I hereby authorize the
            release of such information.
          </Paragraph>
          <Paragraph>
            I understand that the information release/exchange will be treated in a confidential manner and will not be
            released to other persons or agencies without my specific authorization. This authorization expires a year
            from the date of my signature. I understand I have the right to revoke this consent at any time in writing
            except to the extent that information has already been released.
          </Paragraph>
          <Check label="I acknowledge and consent to this release" name="release_consent_acknowledgement" />
        </Section>
      </PageGate>
    </FormPage>
  )
}

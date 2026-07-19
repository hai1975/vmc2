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

/** From https://github.com/hai1975/form-builder-pro child-vn — wired to VMC3 field ids */
export function ChildVnForm() {
  return (
    <FormPage title="ĐƠN GHI DANH BỆNH NHÂN MỚI (TRẺ EM)">
      <PageGate page={1}>
        <Field label="Họ và tên bệnh nhân" name="patient_name" />
        <Row>
          <Field label="Ngày sinh" name="birthday" type="date" />
          <Field label="Số SSN" name="ssn" />
        </Row>
        <Row>
          <Field label="Người giám hộ hợp pháp" name="guardian_1_name" />
          <Field label="Mối quan hệ" name="guardian_1_relationship" />
        </Row>
        <Row>
          <Field label="Người giám hộ hợp pháp" name="guardian_2_name" />
          <Field label="Mối quan hệ" name="guardian_2_relationship" />
        </Row>
        <TextArea label="Địa chỉ nhà" name="home_address" />
        <Row>
          <Field label="Số điện thoại" name="phone" />
          <Field label="Email" name="email" type="email" />
        </Row>

        <CheckGroup
          title="Bảo hiểm"
          name="insurance"
          items={[
            { label: 'Medi-Cal', value: 'medi_cal' },
            { label: 'PPO', value: 'ppo' },
            { label: 'HMO', value: 'hmo' },
            { label: 'Không có', value: 'uninsured' },
          ]}
        />
        <CheckGroup
          title="Chủng tộc"
          name="race"
          multi
          items={[
            { label: 'Châu Á', value: 'asian' },
            { label: 'Da trắng', value: 'white' },
            { label: 'Người Mỹ gốc Phi', value: 'african_american' },
            { label: 'Người da đỏ bản địa hoặc người Alaska bản địa', value: 'native_american' },
            { label: 'Người Hawaii bản địa hoặc người đảo Thái Bình Dương khác', value: 'pacific_islander' },
            { label: 'Khác', value: 'other' },
          ]}
        />
        <Field label="Chủng tộc khác, xin ghi rõ" name="race_other_specify" />
        <CheckGroup
          title="Dân tộc"
          name="ethnicity"
          items={[
            { label: 'Gốc Tây Ban Nha hoặc La-tinh', value: 'hispanic' },
            { label: 'Không gốc Tây Ban Nha hoặc La-tinh', value: 'not_hispanic' },
            { label: 'Không rõ', value: 'unknown' },
          ]}
        />
        <CheckGroup
          title="Giới tính"
          name="gender_identity"
          items={[
            { label: 'Nam', value: 'male' },
            { label: 'Nữ', value: 'female' },
            { label: 'Chọn không tiết lộ', value: 'not_disclose' },
            { label: 'Nữ chuyển sang Nam (FTM)', value: 'ftm' },
            { label: 'Nam chuyển sang Nữ (MTF)', value: 'mtf' },
            { label: 'Giới tính phi nhị nguyên', value: 'genderqueer' },
            { label: 'Khác', value: 'other' },
          ]}
        />
        <CheckGroup
          title="Xu hướng tình dục"
          name="sexual_orientation"
          items={[
            { label: 'Đồng tính nữ/nam', value: 'gay_lesbian' },
            { label: 'Dị tính', value: 'straight' },
            { label: 'Song tính', value: 'bisexual' },
            { label: 'Không biết', value: 'unknown' },
            { label: 'Chọn không tiết lộ', value: 'not_disclose' },
            { label: 'Khác', value: 'other' },
          ]}
        />
        <Row>
          <Field label="Tên nhà thuốc" name="pharmacy_name" />
          <Field label="Số điện thoại nhà thuốc" name="pharmacy_phone" />
        </Row>

        <Section title="ĐỒNG Ý ĐIỀU TRỊ">
          <Paragraph>
            Tôi cho phép Phòng khám VM và các chuyên gia y tế đánh giá và điều trị bệnh nhân. Tôi chịu trách nhiệm thanh
            toán các dịch vụ, bao gồm khoản không được bảo hiểm chi trả.
          </Paragraph>
          <Check label="Đồng ý điều trị" name="treatment_consent" />
        </Section>
      </PageGate>

      <PageGate page={2}>
        <Section title="BỆNH LÝ VÀ TIỀN SỬ XÃ HỘI">
          <Row>
            <Field label="Họ tên bệnh nhân" name="medical_history_patient_name" />
            <Field label="Ngày sinh" name="medical_history_dob" type="date" />
          </Row>
          <div>
            <p className="font-medium mb-1">Đã từng mắc hoặc được chẩn đoán các bệnh sau?</p>
            <div className="flex flex-wrap gap-y-2">
              <Check label="Tiểu đường" name="med_cond_diabetes" />
              <Check label="Cao huyết áp" name="med_cond_high_blood_pressure" />
              <Check label="Cao mỡ" name="med_cond_high_cholesterol" />
              <Check label="Bệnh tim" name="med_cond_heart_disease" />
              <Check label="Hen suyễn" name="med_cond_asthma" />
              <Check label="Đột quỵ" name="med_cond_stroke" />
              <Check label="Bệnh thận" name="med_cond_kidney_disease" />
              <Check label="Bệnh gan" name="med_cond_liver_disease" />
              <Check label="Động kinh" name="med_cond_seizures" />
              <Check label="Ung thư" name="med_cond_cancer" />
              <Check label="Bệnh lý tâm thần" name="med_cond_mental_health" />
            </div>
          </div>
          <Field label="Loại ung thư" name="cancer_type" />
          <Field label="Bệnh khác" name="other_medical_conditions" />
          <TextArea label="Vui lòng liệt kê các ca phẫu thuật và thời gian" name="surgeries" />
          <TextArea label="Vui lòng liệt kê tất cả các loại thuốc đang sử dụng" name="current_medications" rows={3} />
          <YesNoCheck title="Có nhập viện trong 6 tháng qua?" name="hospitalized_6_months" yesLabel="Có" noLabel="Không" />
          <TextArea label="Nếu có, vui lòng ghi rõ" name="hospitalized_details" />
          <Check label="Không có dị ứng" name="no_known_allergies" />
          <Field label="Dị ứng thuốc" name="medication_allergies" />
          <Field label="Dị ứng thực phẩm" name="food_allergies" />
          <Field label="Dị ứng môi trường" name="environmental_allergies" />
          <Row>
            <Field label="Người chăm sóc chính" name="main_caretaker" />
            <Field label="Mối quan hệ" name="caretaker_relationship" />
          </Row>
          <TextArea label="Thuốc hoặc biến chứng trong thời kỳ mang thai" name="pregnancy_complications" />
          <Field label="Khi nào mẹ dự định quay trở lại các hoạt động bình thường sau sinh?" name="mother_return_activities" />
          <Field label="Bệnh nhân/trẻ đang bú mẹ hay uống sữa công thức?" name="breastfeeding_or_formula" />
          <YesNoCheck title="Đang sử dụng ghế an toàn trên xe hơi?" name="uses_car_seat" yesLabel="Có" noLabel="Không" />
        </Section>
      </PageGate>

      <PageGate page={3}>
        <Section title="TIỀN SỬ GIA ĐÌNH & LỐI SỐNG">
          <CheckGroup
            title="Gia đình có ai mắc các bệnh sau?"
            name="family_history"
            multi
            items={[
              { label: 'Tiểu đường', value: 'diabetes' },
              { label: 'Ung thư', value: 'cancer' },
              { label: 'Bệnh tim', value: 'heart_disease' },
              { label: 'Cao huyết áp', value: 'high_blood_pressure' },
              { label: 'Đột quỵ', value: 'stroke' },
              { label: 'Bệnh tâm thần', value: 'mental_illness' },
              { label: 'Khác', value: 'other' },
            ]}
          />
          <Field label="Khác" name="family_history_other" />
          <YesNoCheck title="Có tiếp xúc với khói thuốc lá thụ động trong gia đình?" name="secondhand_smoke" yesLabel="Có" noLabel="Không" />
          <YesNoCheck title="Hút thuốc?" name="tobacco_use" yesLabel="Có" noLabel="Không" />
          <Field label="Hút thuốc (bao nhiêu/lần bao lâu)" name="tobacco_frequency" />
          <YesNoCheck title="Uống rượu?" name="alcohol_use" yesLabel="Có" noLabel="Không" />
          <Field label="Rượu (bao nhiêu/lần bao lâu)" name="alcohol_frequency" />
          <YesNoCheck title="Thuốc gây nghiện?" name="recreational_drugs" yesLabel="Có" noLabel="Không" />
          <Field label="Liệt kê" name="recreational_drugs_list" />
          <YesNoCheck
            title="Cha/mẹ hoặc người giám hộ có sử dụng thuốc gây nghiện hoặc uống rượu quá mức?"
            name="parent_drug_alcohol"
            yesLabel="Có"
            noLabel="Không"
          />
          <YesNoCheck title="Cảm thấy an toàn nơi đang sống?" name="feel_safe_home" yesLabel="Có" noLabel="Không" />
          <CheckGroup
            title="Đã tiêm chủng đầy đủ?"
            name="vaccinations_up_to_date"
            items={[
              { label: 'Có', value: 'yes' },
              { label: 'Không', value: 'no' },
              { label: 'Không chắc', value: 'unsure' },
            ]}
          />
          <CheckGroup
            title="Đã xét nghiệm lao?"
            name="tb_tested"
            items={[
              { label: 'Có', value: 'yes' },
              { label: 'Không', value: 'no' },
              { label: 'Không chắc', value: 'unsure' },
            ]}
          />
          <CheckGroup
            title="Nếu có, kết quả?"
            name="tb_result"
            items={[
              { label: 'Âm tính', value: 'negative' },
              { label: 'Dương tính', value: 'positive' },
              { label: 'Không chắc', value: 'unsure' },
            ]}
          />
          <YesNoCheck title="Yêu cầu đặc biệt về giao tiếp?" name="communication_requirements" yesLabel="Có" noLabel="Không" />
          <Field label="Nếu có, vui lòng ghi rõ" name="communication_details" />
          <YesNoCheck title="Cần thông dịch?" name="interpretation_needed" yesLabel="Có" noLabel="Không" />
          <Field label="Nếu có, ngôn ngữ nào?" name="interpretation_language" />
        </Section>

        <Section title="XÁC NHẬN THÔNG BÁO VỀ QUYỀN RIÊNG TƯ">
          <Paragraph>
            Bằng cách ký vào biểu mẫu này, quý vị xác nhận đã nhận được Thông Báo Về Quyền Riêng Tư của Phòng khám VM
            (www.vmclinic.us).
          </Paragraph>
          <Check label="Tôi xác nhận" name="hipaa_acknowledgement" />
        </Section>

        <Section title="CHO PHÉP CUNG CẤP THÔNG TIN">
          <Row>
            <Field label="Tên" name="release_contact_1_name" />
            <Field label="Mối quan hệ" name="release_contact_1_relationship" />
          </Row>
          <Row>
            <Field label="Số điện thoại" name="release_contact_1_phone" />
            <YesNoCheck title="Liên hệ khẩn cấp" name="release_contact_1_emergency" yesLabel="Có" noLabel="Không" />
          </Row>
          <Row>
            <Field label="Tên" name="release_contact_2_name" />
            <Field label="Mối quan hệ" name="release_contact_2_relationship" />
          </Row>
          <Row>
            <Field label="Số điện thoại" name="release_contact_2_phone" />
            <YesNoCheck title="Liên hệ khẩn cấp" name="release_contact_2_emergency" yesLabel="Có" noLabel="Không" />
          </Row>
        </Section>
      </PageGate>

      <PageGate page={4}>
        <Section title="ĐỒNG Ý LIÊN LẠC ĐIỆN TỬ">
          <Paragraph>
            Tôi đồng ý và cho phép Phòng khám VM liên lạc qua điện thoại, tin nhắn, email và các hình thức điện tử khác.
          </Paragraph>
          <Check label="Tôi đồng ý" name="electronic_communication_consent" />
          <Field label="Họ tên bệnh nhân (hoặc người đại diện)" name="consent_signer_name" />
        </Section>

        <Section title="AUTHORIZATION FOR RELEASE INFORMATION">
          <Row>
            <Field label="Tên bệnh nhân" name="authorization_patient_name" />
            <Field label="Ngày sinh" name="authorization_dob" type="date" />
          </Row>
          <Field label="Tôi, ___ cho phép" name="release_authorization_name" />
          <Paragraph>
            Hồ sơ được cung cấp cho VM Medical Group như in trên biểu mẫu này. Quý vị không cần ghi tên bệnh viện hoặc cơ
            sở y tế khác.
          </Paragraph>
          <CheckGroup
            title="Thông tin được cung cấp"
            name="records_to_release"
            multi
            items={[
              { label: 'Toàn bộ hồ sơ y tế', value: 'complete_record' },
              { label: 'Bệnh án', value: 'office_notes' },
              { label: 'Kết quả xét nghiệm', value: 'lab_reports' },
              { label: 'Hình ảnh/X-quang', value: 'radiology' },
              { label: 'Hồ sơ tiêm chủng', value: 'immunization' },
              { label: 'Hồ sơ thuốc', value: 'medication_records' },
              { label: 'Khác', value: 'other' },
            ]}
          />
          <CheckGroup
            title="Mục đích cung cấp thông tin"
            name="disclosure_purpose"
            multi
            items={[
              { label: 'Tiếp tục điều trị', value: 'continuation_of_care' },
              { label: 'Sử dụng cá nhân', value: 'personal_use' },
              { label: 'Pháp lý', value: 'legal' },
              { label: 'Bảo hiểm', value: 'insurance' },
              { label: 'Theo dõi sau khi nhập viện', value: 'post_hospital' },
              { label: 'Khác', value: 'other' },
            ]}
          />
          <Paragraph>
            Mục đích của việc tiết lộ thông tin này là để bảo đảm sự liên tục trong chăm sóc y tế. Việc trao đổi thông tin
            giúp đảm bảo sự liên kết và phối hợp giữa các nhà cung cấp dịch vụ y tế, và nếu không có sự trao đổi này, việc
            chăm sóc sức khỏe của tôi có thể bị ảnh hưởng. Tôi hiểu rằng các thông tin cụ thể liên quan đến tình trạng tâm
            thần, xét nghiệm HIV và kết quả, cũng như các chẩn đoán và tình trạng y tế liên quan có thể được ghi nhận trong
            hồ sơ sức khỏe của tôi. Tôi đồng ý cho phép tiết lộ các thông tin này.
          </Paragraph>
          <Paragraph>
            Tôi hiểu rằng việc tiết lộ/trao đổi thông tin này sẽ được xử lý một cách bảo mật và sẽ không được cung cấp cho
            bất kỳ cá nhân hoặc tổ chức nào khác nếu không có sự cho phép cụ thể của tôi. Sự cho phép này sẽ hết hạn sau một
            năm kể từ ngày tôi ký tên. Tôi hiểu rằng tôi có quyền hủy bỏ sự đồng ý này bất cứ lúc nào bằng văn bản, trừ khi
            thông tin đã được tiết lộ trước thời điểm đó.
          </Paragraph>
          <Check label="Tôi xác nhận và đồng ý cung cấp hồ sơ" name="release_consent_acknowledgement" />
        </Section>
      </PageGate>

      <PageGate page={5}>
        <Paragraph>Signature area on PDF</Paragraph>
      </PageGate>
    </FormPage>
  )
}

import argparse
import csv

import jaconv
import vobject

from lib_normalize_tel_num import normalize_tel_num


def main(input_vcf_fh, output_csv_fh, no_my_contacts: bool):
    max_num_of_address, max_num_of_email, max_num_of_phone, max_num_of_url, phonebook = load_vcf(input_vcf_fh, no_my_contacts)
    write_to_csv(output_csv_fh, phonebook, max_num_of_address, max_num_of_email, max_num_of_phone, max_num_of_url)


def load_vcf(input_vcf_fh, no_my_contacts: bool):
    # 電話・メール種別変換関数定義
    def tel_email_type_convert(type_str: str) -> str:
        if type_str == "HOME":
            return "Home"
        elif type_str == "COMPANY":
            return "Work"
        elif type_str == "CELL":
            return "Mobile"
        else:
            return "Other"

    # VCF読み込み
    vcf = vobject.readComponents(input_vcf_fh, allowQP=True)
    max_num_of_phone = 0
    max_num_of_email = 0
    max_num_of_address = 0
    max_num_of_url = 0
    phonebook = []
    for record in vcf:
        given_name = ""
        family_name = ""
        name = ""
        if "n" in record.contents:
            given_name = jaconv.h2z(record.contents["n"][0].value.given, kana=True, ascii=False, digit=False)
            family_name = jaconv.h2z(record.contents["n"][0].value.family, kana=True, ascii=False, digit=False)
            name = " ".join(list(filter(lambda x: x != "", [family_name, given_name])))

        family_yomi = ""
        given_yomi = ""
        yomi = ""
        if "sound" in record.contents:
            family_yomi, given_yomi, _ = record.contents["sound"][0].value.split(";")
            yomi = " ".join(list(filter(lambda x: x != "", [family_yomi, given_yomi])))
            del _

        tels = []
        if "tel" in record.contents:
            for base_tel in record.contents["tel"]:
                normalized_tel = normalize_tel_num(base_tel.value)
                if len(base_tel.singletonparams) > 0 and base_tel.singletonparams[0] != "":
                    converted_type = tel_email_type_convert(base_tel.singletonparams[0])
                elif normalized_tel.startswith(("090", "080", "070")):
                    converted_type = "Mobile"
                else:
                    converted_type = "Other"
                tels.append((converted_type, normalized_tel))
                del base_tel, normalized_tel, converted_type
        max_num_of_phone = max(max_num_of_phone, len(tels))

        addresses = []
        if "adr" in record.contents:
            for base_address in record.contents["adr"]:
                address = base_address.value
                if address.code != "" or address.region != "" or address.city != "" or address.street != "":
                    addresses.append((address.code, address.region, address.city, address.street))
                del base_address, address
        max_num_of_address = max(max_num_of_address, len(addresses))

        emails = []
        if "email" in record.contents:
            for base_email in record.contents["email"]:
                if base_email.value != "":
                    email = base_email.value
                    if len(base_email.singletonparams) > 0 and base_email.singletonparams[0] != "":
                        converted_type = tel_email_type_convert(base_email.singletonparams[0])
                    else:
                        if base_email.value.endswith(("ezweb.ne.jp", "docomo.ne.jp", "softbank.ne.jp", "vodafone.ne.jp",
                                                      "i.softbank.jp", "biz.ezweb.ne.jp", "emobile.ne.jp",
                                                      "emobile-s.ne.jp", "ymobile1.ne.jp", "ymobile.ne.jp",
                                                      "yahoo.ne.jp", "willcom.com", "y-mobile.ne.jp")):
                            converted_type = "Mobile"
                        else:
                            converted_type = "Other"
                    emails.append((converted_type, email))
                    del email, converted_type
                del base_email
        max_num_of_email = max(max_num_of_email, len(emails))

        if no_my_contacts:
            groups = []
        else:
            groups = ["* My Contacts"]
        if "x-dcm-gn-original" in record.contents:
            for group in record.contents["x-dcm-gn-original"]:
                if group.value != "":
                    groups.append(jaconv.normalize(group.value))
                del group
        elif "x-gn" in record.contents:
            groups.append(jaconv.normalize(record.contents["x-gn"]))

        birthday = ""
        if "bday" in record.contents and record.contents["bday"][0].value != "":
            birthday = "-".join([
                record.contents["bday"][0].value[0:4],
                record.contents["bday"][0].value[4:6],
                record.contents["bday"][0].value[6:8]
            ])

        urls = []
        if "url" in record.contents:
            for base_url in record.contents["url"]:
                if base_url.value != "":
                    urls.append(base_url.value)
                del base_url
        max_num_of_url = max(max_num_of_url, len(urls))

        note = ""
        if "note" in record.contents:
            note = record.contents["note"][0].value

        phonebook.append({
            "given_name": given_name,
            "family_name": family_name,
            "name": name,
            "given_yomi": given_yomi,
            "family_yomi": family_yomi,
            "yomi": yomi,
            "tels": tels,
            "addresses": addresses,
            "emails": emails,
            "groups": groups,
            "birthday": birthday,
            "urls": urls,
            "note": note
        })
    return max_num_of_address, max_num_of_email, max_num_of_phone, max_num_of_url, phonebook


def write_to_csv(output_csv_fh, phonebook, max_num_of_address, max_num_of_email, max_num_of_phone, max_num_of_url):
    # ライター初期化
    google_csv = csv.writer(output_csv_fh)

    # CSVヘッダ行作成・書き込み
    csv_headers = ["Name", "Given Name", "Additional Name", "Family Name", "Yomi Name", "Given Name Yomi",
                   "Additional Name Yomi", "Family Name Yomi", "Name Prefix", "Name Suffix", "Initials",
                   "Nickname", "Short Name", "Maiden Name", "Birthday", "Gender", "Location",
                   "Billing Information", "Directory Server", "Mileage", "Occupation", "Hobby", "Sensitivity",
                   "Priority", "Subject", "Notes", "Group Membership"]
    for i in range(1, max_num_of_phone + 1):
        csv_headers.extend(["Phone {} - Type".format(i), "Phone {} - Value".format(i)])
    for i in range(1, max_num_of_address + 1):
        csv_headers.extend(
            ["Address {} - Formatted".format(i), "Address {} - Street".format(i), "Address {} - City".format(i),
             "Address {} - PO Box".format(i), "Address {} - Region".format(i), "Address {} - Postal Code".format(i),
             "Address {} - Country".format(i), "Address {} - Extended Address".format(i)])
    for i in range(1, max_num_of_email + 1):
        csv_headers.extend(["E-mail {} - Type".format(i), "E-mail {} - Value".format(i)])
    for i in range(1, max_num_of_url + 1):
        csv_headers.extend(["Website {} - Type".format(i), "Website {} - Value".format(i)])
    google_csv.writerow(csv_headers)

    # CSVデータ行書き込み
    for p in phonebook:
        csv_row = [
            p["name"], p["given_name"], "", p["family_name"], p["yomi"], p["given_yomi"], "", p["family_yomi"],
            "", "", "", "", "", "", p["birthday"], "", "", "", "", "", "", "", "", "", "", p["note"],
            " ::: ".join(p["groups"])
        ]

        for phone in p["tels"]:
            csv_row.extend(phone)
        for i in range(len(p["tels"]), max_num_of_phone):
            csv_row.extend(["", ""])

        for address in p["addresses"]:
            csv_row.extend([
                "{}{}{}".format(address[1], address[2], address[3]),
                address[3],
                address[2],
                "",
                address[1],
                address[0],
                "",
                ""
            ])
        for i in range(len(p["addresses"]), max_num_of_address):
            csv_row.extend(["", "", "", "", "", "", "", ""])

        for email in p["emails"]:
            csv_row.extend(email)
        for i in range(len(p["emails"]), max_num_of_email):
            csv_row.extend(["", ""])

        for url in p["urls"]:
            csv_row.extend(["Other", url])
        for i in range(len(p["urls"]), max_num_of_url):
            csv_row.extend(["", ""])

        google_csv.writerow(csv_row)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Converts from VCF exported by docomo phone book to CSV of Google contact import format.")
    parser.add_argument("Input_VCF", type=argparse.FileType("r"), help="Input VCF FilePath")
    parser.add_argument("Output_CSV", type=argparse.FileType("w"), help="Output CSV FilePath")
    parser.add_argument("--no-my-contacts", action="store_true", help="Do not add \"My Contacts\" group.")
    args = parser.parse_args()
    main(args.Input_VCF, args.Output_CSV, args.no_my_contacts)

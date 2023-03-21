#!/usr/bin/python
# -*- coding: ISO-8859-15 -*-
# =============================================================================
# Copyright (c) 2019 Mundi Web Services
# Licensed under the 3-Clause BSD License; you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
# https://opensource.org/licenses/BSD-3-Clause
#
# Author : Patricia Segonds
#
# Contact email: patricia.segonds@atos.net
# =============================================================================

from __future__ import annotations

# standard library imports
import logging
import os
from os.path import basename, dirname, join
from typing import Any, Dict, Iterable, List, Union

# other imports
import boto3
from lxml import etree
from owslib.csw import CatalogueServiceWeb, CswRecord
from owslib.util import openURL, OrderedDict, ResponseWrapper
from owslib.wcs import WebCoverageService
from owslib.wfs import WebFeatureService
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService

# custom modules imports
# import utils


# Mundi collections ids
# TODO: addition of other ids (from Landsat, Sentinel3, ...)
MUNDI_COLLECTION_IDS = {
    'Sentinel1-GRD': "88b68ca0-1f84-4286-8359-d3f480771de5",
    'Sentinel2-L1C': "d275ef59-3f26-4466-9a60-ff837e572144",
    'Sentinel2-L2A': "ea23bfb3-2a67-476f-90e3-fe54873ff897",
    'Sentinel5P-L2': "9400667f-cb51-4509-8827-44232ccd507f",
    'Landsat8-L2': "aca4e8e1-7855-4de0-8fe0-096c02859aa8"
}

# web services endpoints
MUNDI_SERVICES_ENDPOINTS = {
    'wms': "http://shservices.mundiwebservices.com/ogc/wms/",
    'wmts': "http://shservices.mundiwebservices.com/ogc/wmts/",
    'wfs': "http://shservices.mundiwebservices.com/ogc/wfs/",
    'wcs': "http://shservices.mundiwebservices.com/ogc/wcs/",
    'wms_l8': "http://services-uswest2.sentinel-hub.com/ogc/wms/"
}

# NOTE: above information should be gotten from CSW discovery

# all namespaces used by Mundi
MUNDI_NAMESPACES = {
    'atom': "http://www.w3.org/2005/Atom",
    'csw': "http://www.opengis.net/cat/csw/2.0.2",
    'dc': "http://purl.org/dc/elements/1.1/",
    'dct': "http://purl.org/dc/terms/",
    'DIAS': "http://mundi/DIAS",
    'eo': "http://a9.com/-/spec/opensearch/extensions/eo/1.0/",
    'geo': "http://a9.com/-/opensearch/extensions/geo/1.0/",
    'georss': "http://www.georss.org/georss",
    'media': "http://search.yahoo.com/mrss/",
    'os': "http://a9.com/-/spec/opensearch/1.1/",
    'ows': "http://www.opengis.net/ows",
    'param': "http://a9.com/-/spec/opensearch/extensions/parameters/1.0/",
    'referrer': "http://www.opensearch.org/Specifications/OpenSearch/Extensions/Referrer/1.0",
    'sru': "http://a9.com/-/opensearch/extensions/sru/2.0/",
    'time': "http://a9.com/-/opensearch/extensions/time/1.0/",
    'xmlns': "http://www.w3.org/2001/XMLSchema",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance"
}

MUNDI_COLLECTIONS = ["Sentinel1", "Sentinel2", "Sentinel3", "Sentinel5p", "Landsat8"]

# logger config
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s'))
logger.addHandler(sh)


# --------------------------
#  EXCEPTIONS
# --------------------------
class ErrorMessages:
    UNSUPPORTED_SERVICE = "Unsupported web service version requested."
    UNAVAILABLE_COLLECTION = "Unavailable collection."
    UNAVAILABLE_COLLECTION_SERVICE = "Unavailable service on collection."


class MundiException(Exception):
    pass


# --------------------------
# CATALOGUE
# --------------------------
class MundiCatalogue:
    # csw entry point
    csw_end_point = "https://sentinel2.browse.catalog.mundiwebservices.com/csw"

    def __init__(self):
        # fill collections property with MundiCollection for all supported platforms
        self.collections = [MundiCollection(p) for p in MUNDI_COLLECTIONS]

    def get_collection(self, name):
        """
        Get a collection from this instance's collections list

        :param name: name of the collection
        :return: the collection as a MundiCollection instance
        """
        for c in self.collections:
            if c.name == name:
                return c

        raise MundiException(ErrorMessages.UNAVAILABLE_COLLECTION)

    def mundi_csw(self, version="2.0.2"):
        """
        Get a MundiCSW instance

        :param version: CSW version. Defaults to 2.0.2
        :return: a MundiCSW instance
        """
        if version in ["2.0.2"]:
            return MundiCSW(self.csw_end_point, version)
        else:
            raise MundiException(ErrorMessages.UNSUPPORTED_SERVICE)

    # ---------------------------------
    # Functions for retro compatibility
    # ---------------------------------
    def get_collections(self):
        logger.warning(
            'This function will be removed in future versions of mundilib. In order to for you code to run with these '
            'future versions, please consider using "collections" property instead')
        return self.collections

    def getCollections(self):
        logger.warning(
            'This function will be removed in future versions of mundilib. In order to for you code to run with these '
            'future versions, please consider using "collections" property instead')
        return self.collections

    def getCollection(self, name):
        logger.warning(
            'This function will be removed in future versions of mundilib. In order to for you code to run with these '
            'future versions, please consider using "get_collection" function instead')
        return self.get_collection(name)


# --------------------------
# CSW
# --------------------------
class MundiCSW(CatalogueServiceWeb):

    def __init__(self, url, version):
        self.records = None
        super().__init__(url, version)

    def describe_record(self):
        """
        Send a DescribeRecord request and process it. Return metadata as a dict

        :return: as dict of metadata
        """
        # getting root node from 'DescribeRecord' request
        # from https://github.com/geopython/OWSLib/blob/master/owslib/csw.py:
        # TODO: process the XML Schema (you're on your own for now with self.response)
        self.describerecord(typename='csw:Record', format='application/xml')
        root = etree.fromstring(self.response)

        # getting node containing all elements
        # (i.e. '<complexType name="RecordType" final="#all">')
        node = root.find('.//csw:SchemaComponent/xmlns:schema/xmlns:complexType[@name="RecordType"]',
                         namespaces=MUNDI_NAMESPACES)
        nodes = node.findall('.//*xmlns:element', namespaces=MUNDI_NAMESPACES)

        elements = {}
        for n in nodes:
            d = n.find(".//*xmlns:documentation", namespaces=MUNDI_NAMESPACES)
            if d is not None:
                elements[n.get('ref')] = d.text.replace("\n", "")
        return elements

    def get_records(self, maxrecords=50, **kwargs):
        """
        Send a GetRecords request. The results are stored in self.records property.

        :param kwargs: see OWSLib's getrecords2 (https://github.com/geopython/OWSLib/blob/master/owslib/csw.py).
        A hint: if "xml" argument is passed (raw WML request), other arguments are ignored. Also, if maxrecords exceeds
        50, getrecords2 is called multiple times to get maxrecords records (or less if less are found)
        """
        # Always set Element Set Name because OWSLib can't read Element Name
        kwargs['esn'] = 'full'
        # has xml argument been passed?
        try:
            payload = kwargs['xml'].strip()
        except KeyError:
            payload = None

        # all 'csw:Record' dict from 'GetRecords' request pages
        all_records = OrderedDict()

        while True:
            # set kwargs' maxrecords according to how many records we want (doesn't matter if it exceeds 50)
            kwargs['maxrecords'] = min(maxrecords, maxrecords - len(all_records))

            # get next page by using OWSLib's getrecords2
            if payload is None:
                self.getrecords2(**kwargs)
            else:
                self.getrecords2(xml=payload)

            # store found records in all_records
            all_records.update(self.records)

            # stop if records reached limit
            if len(all_records) >= maxrecords:
                break

            next_record = self.results['nextrecord']
            # if next_record is "0", we got all records
            if next_record == 0:
                break

            # else, update start position
            if payload is None:
                kwargs['startposition'] = next_record
            else:
                payload_xml = etree.fromstring(payload)
                payload_xml.set('startPosition', str(next_record))
                payload = etree.tostring(payload_xml, pretty_print=True, encoding='unicode')

        self.records = all_records

    def get_volume_records(self, **kwargs):
        """
        Get an approximation of the total volume of records matched by a request
        (ie, sum of records' productDatapackSize)

        :param kwargs: see OWSLib's getrecords2 (https://github.com/geopython/OWSLib/blob/master/owslib/csw.py).
        A hint: if "xml" argument is passed (raw WML request), other arguments are ignored. Therefore, if using "xml",
        productDatapackSize should be requested (<ElementSetName>full</ElementSetName> or
        <ElementName>productDatapackSize</ElementName>)
        :return: sum of all productDatapackSize in TB
        """
        # we need to get all records at first
        kwargs['esn'] = 'full'
        self.get_records(**kwargs)

        # sum of DIAS:productDatapackSize
        volume = 0
        for csw_record in self.records.values():
            node = etree.fromstring(csw_record.xml)
            node_size = node.find("DIAS:productDatapackSize", namespaces=MUNDI_NAMESPACES)
            if node_size is not None:
                volume += float(node_size.text)

        # convert to TB and round to two decimals
        return round(volume / 1024 ** 4, 2)

    def get_nb_records(self, **kwargs):
        """
        Get number of records matched by a GetRecord request

        :param kwargs: see OWSLib's getrecords2 (https://github.com/geopython/OWSLib/blob/master/owslib/csw.py).
        A hint: if "xml" argument is passed (raw WML request), other arguments are ignored. "maxrecords" is ignored
        and set to 0.
        :return: number of records (i.e. 'numberOfRecordsMatched' value)
        """
        kwargs['maxrecords'] = 0
        # No need to load all metadata here
        kwargs['esn'] = 'brief'
        # get only first page
        self.getrecords2(**kwargs)
        return int(int(self.results['matches']))

    # ---------------------------------
    # Functions for retro compatibility
    # ---------------------------------
    def mundigetrecords2(self, xml):
        logger.warning(
            'This function will be removed in future versions of mundilib. In order to for you code to run with these '
            'future versions, please consider using "get_records" function instead')
        return self.get_records(xml=xml)

    def mundigetvolrecords2(self, xml):
        logger.warning(
            'This function will be removed in future versions of mundilib. In order to for you code to run with these '
            'future versions, please consider using "get_volume_records" function instead')
        return self.get_volume_records(xml=xml)

    def mundigetnbrecords2(self, xml):
        logger.warning(
            'This function will be removed in future versions of mundilib. In order to for you code to run with these '
            'future versions, please consider using "get_nb_records" function instead')
        return self.get_nb_records(xml=xml)


# --------------------------
# DOWNLOADER
# --------------------------
class MundiDownloader:

    def __init__(self, collection: MundiCollection, access_key: str, secret_key: str):
        self.csw = collection.mundi_csw()
        self.s3_client = boto3.client("s3", aws_access_key_id=access_key,
                                      aws_secret_access_key=secret_key,
                                      endpoint_url="https://obs.otc.t-systems.com")

    @property
    def records(self):
        return self.csw.records

    def browse(self, date_from: str = None, date_to: str = None, geometry: str = None,
               bbox: Iterable[Union[float, int, str]] = None, other_fields: Dict[str, Any] = None):
        """
        Browse catalog and store results in "records" property.
        :param date_from: date from which to search products
        :param date_to: date until which to search products
        :param geometry: a WKT geometry, basically a POLYGON, eg "POLYGON ((0 1, 2 1, 2 0, 0 0, 0 1))". Ignored if bbox is specified
        :param bbox: a bounding box (longitude min, latitude min, longitude max, latitude max), eg (1., 0., 3., 4.)
        :param other_fields: any other CQL filter terms, eg: {"DIAS:sensorMode": "IW_"}
        """
        # build CQL filter
        cql_filter = f"DIAS:onlineStatus = ONLINE"
        if date_from is not None:
            cql_filter = f"{cql_filter} and DIAS:sensingStartDate &gt; '{date_from}'"
        if date_to is not None:
            cql_filter = f"{cql_filter} and DIAS:sensingStartDate &lt; '{date_to}'"

        if bbox is not None:
            cql_filter = f"{cql_filter} and BBOX(DIAS:footprint,ENVELOPE({', '.join(str(x) for x in bbox)}))"
        # geometry must be ignored if bbox is specified
        elif geometry is not None:
            cql_filter = f"{cql_filter} and INTERSECTS(DIAS:footprint, {geometry})"

        # add any other specified field
        if other_fields is not None:
            for field, value in other_fields.items():
                cql_filter = f"{cql_filter} and {field} = '{value}'"

        xml_string = f'''<GetRecords xmlns='http://www.opengis.net/cat/csw/2.0.2'
                    xmlns:DIAS='http://mundiwebservices.com/DIAS'
                    xmlns:csw='http://www.opengis.net/cat/csw/2.0.2'
                    xmlns:dc='http://purl.org/dc/elements/1.1/'
                    xmlns:dct='http://purl.org/dc/terms/'
                    xmlns:gml='http://www.opengis.net/gml'
                    xmlns:ogc='http://www.opengis.net/ogc'
                    xmlns:ows='http://www.opengis.net/ows'
                    xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'
                    service='CSW' version='2.0.2' maxRecords='50' startPosition='1' resultType='results'
                    outputFormat='application/xml' outputSchema='csw:Record' xsi:schemaLocation='http://www.opengis.net/cat/csw/2.0.2/CSW-discovery.xsd'>
                    <csw:Query typeNames='csw:Record'>
                        <csw:ElementSetName>full</csw:ElementSetName>
                        <csw:Constraint version='1.1.0'>
                            <csw:CqlText> {cql_filter}
                            </csw:CqlText>
                        </csw:Constraint>
                    </csw:Query>
                </GetRecords>'''

        # search the catalog
        self.csw.get_records(xml=xml_string)

    def download(self, target_folder: str = "."):
        """
        Download products, based on "records" property content
        :param target_folder: the folder where to download products
        """
        # iterate results & download them
        for id_, record in self.records.items():
            self._download_product(id_, record, target_folder)

    def download_by_id(self, record_id: str, target_folder: str = "."):
        """
        Download a specific record
        :param record_id: the identifier of this record
        :param target_folder: the folder where to download this product
        """
        # retrieve the ID from the catalog
        self.csw.get_records(cql=f"dc:identifier = {record_id}", esn="full")
        try:
            record = self.records[record_id]
        except KeyError:
            raise ValueError(f"Failed to find a record with ID '{record_id}'")

        # download the product
        self._download_product(record_id, record, target_folder)

    def _download_product(self, record_id: str, record: CswRecord, target_folder: str):
        logger.info(f"Downloading {record_id}")

        # get bucket & prefix from URI
        uri = get_node(record, "DIAS:archiveProductURI").text
        bucket, prefix = uri.split(".com/")[-1].split("/", 1)

        # find out what's within this prefix (there should not be more than 1000 keys)
        list_contents = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)["Contents"]

        if len(list_contents) == 0:
            logger.warning(f"Did not find any object at s3://{bucket}/{prefix}")
            return
        elif len(list_contents) == 1:
            # there's a single file for this product, it is archived (zip)
            key = list_contents[0]["Key"]
            self._download_object(bucket, key, join(target_folder, basename(key)))
        elif len(list_contents) > 1:
            # create target folder
            os.makedirs(target_folder, exist_ok=True)

            # this product has been extracted, we must download all the keys one by one
            for key in [x["Key"] for x in list_contents]:
                target_path = join(target_folder, key.replace(dirname(prefix), "").lstrip("/"))
                self._download_object(bucket, key, target_path)

    def _download_object(self, bucket: str, key: str, target_path: str):
        # create target folder
        os.makedirs(dirname(target_path), exist_ok=True)

        # download file
        self.s3_client.download_file(Bucket=bucket, Key=key, Filename=target_path)


# --------------------------
# COLLECTION
# --------------------------
class MundiCollection:

    def __init__(self, name: str):
        # collection name, formatted as in catalog URIs
        self.name = name
        if self.name != "Landsat8":
            # OpenSearch description
            self.opensearch_description = OpenSearchDescription(f'https://{self.name}.browse.catalog.mundiwebservices.com/opensearch/description.xml')

            # CSW endpoint for this collection
            self.csw_endpoint = f'https://{self.name}.browse.catalog.mundiwebservices.com/csw?service=CSW'

    def _service_end_point(self, service: str, dataset: str) -> str:
        """Get service endpoint"""
        try:
            if service == 'wms':
                if self.name == 'Landsat8':
                    return MUNDI_SERVICES_ENDPOINTS['wms_l8'] + MUNDI_COLLECTION_IDS[f'{self.name}-{dataset}']
                else:
                    return MUNDI_SERVICES_ENDPOINTS[service] + MUNDI_COLLECTION_IDS[f'{self.name}-{dataset}']
            else:
                return MUNDI_SERVICES_ENDPOINTS[service] + MUNDI_COLLECTION_IDS[f'{self.name}-{dataset}']
        except KeyError:
            raise MundiException(ErrorMessages.UNAVAILABLE_COLLECTION_SERVICE)

    @property
    def product_types(self) -> Dict:
        """
        Get supported product types for this collection
        :return: all product types for this collection as a dict of {value: label}
        """
        product_type_xml = self.opensearch_description.findall('.//param:Parameter[@name="productType"]/param:Option')
        res = {}

        if product_type_xml is not None:
            for option in product_type_xml:
                res[option.get('value')] = option.get('label')

        return res

    @property
    def processing_levels(self) -> Dict:
        """
        Get supported processing levels for this collection

        :return: all processing levels for this collection as a dict of {value: label}
        """
        processing_levels_xml = self.opensearch_description.findall(
            './/param:Parameter[@name="processingLevel"]/param:Option')
        res = {}

        if processing_levels_xml is not None:
            for option in processing_levels_xml:
                res[option.get('value')] = option.get('label')

        return res

    def mundi_csw(self, version: str = "2.0.2") -> MundiCSW:
        """
        Get a MundiCSW instance for this collection

        :param version: CSW version
        :return: a MundiCSW instance
        """
        if version in ["2.0.2"]:
            return MundiCSW(self.csw_endpoint, version)
        else:
            raise MundiException(ErrorMessages.UNSUPPORTED_SERVICE)

    def mundi_wms(self, dataset: str, version: str = "1.1.1") -> WebMapService:
        """
        Get a WebMapService instance for this collection

        :param dataset: the target dataset (eg, "L1C" if collection is "Sentinel2"
        :param version: WMS version (supported versions are: 1.1.1, 1.3.0)
        :return: a WebMapService instance
        """
        if version in ["1.1.1", "1.3.0"]:
            return WebMapService(self._service_end_point('wms', dataset), version)
        else:
            raise MundiException(ErrorMessages.UNSUPPORTED_SERVICE)

    def mundi_wmts(self, dataset: str, version: str = "1.0.0") -> WebMapTileService:
        """
        Get a WebMapTileService instance for this collection

        :param dataset: the target dataset (eg, "L1C" if collection is "Sentinel1"
        :param version: WMTS version (only 1.0.0 is supported)
        :return: a WebMapTileService instance
        """
        if version in ["1.0.0"]:
            return WebMapTileService(self._service_end_point('wmts', dataset), version)
        else:
            raise MundiException(ErrorMessages.UNSUPPORTED_SERVICE)

    def mundi_wfs(self, dataset: str, version: str = "2.0.0") -> WebFeatureService:
        """
        Get a WebFeatureService instance for this collection

        :param dataset: the target dataset (eg, "L1C" if collection is "Sentinel1"
        :param version: WFS version (only 2.0.0 is supported)
        :return: a WebFeatureService instance
        """
        if version in ["2.0.0"]:
            return WebFeatureService(self._service_end_point('wfs', dataset), version)
        else:
            raise MundiException(ErrorMessages.UNSUPPORTED_SERVICE)

    def mundi_wcs(self, dataset: str, version: str = "1.0.0") -> WebCoverageService:
        """
        Get a WebCoverageService instance for this collection

        :param dataset: the target dataset (eg, "L1C" if collection is "Sentinel1"
        :param version: WCS version (supported versions are: 1.0.0, 1.1.0, 1.1.1, 1.1.2)
        :return: a WebCoverageService instance
        """
        if version in ["1.0.0", "1.1.0", "1.1.1", "1.1.2"]:
            return WebCoverageService(self._service_end_point('wcs', dataset), version)
        else:
            raise MundiException(ErrorMessages.UNSUPPORTED_SERVICE)

    def mundi_downloader(self, access_key: str, secret_key: str) -> MundiDownloader:
        """
        Get a MundiDownloader for this collection

        :param access_key: the access key to authenticate the user to access buckets
        :param secret_key: the secret key to authenticate the user to access buckets
        :return: a MundiDownloader instance
        """
        return MundiDownloader(self, access_key, secret_key)

    # ---------------------------------
    # Functions for retro compatibility
    # ---------------------------------
    def productTypes(self):
        logger.warning(
            'This function will be removed in future versions of mundilib. In order to for you code to run with these '
            'future versions, please consider using "product_types" property instead')
        return self.product_types

    def processingLevels(self):
        logger.warning(
            'This function will be removed in future versions of mundilib. In order to for you code to run with these '
            'future versions, please consider using "processing_levels" property instead')
        return self.processing_levels


# --------------------------
# CSW RECORD
# --------------------------
def get_node(csw_record: CswRecord, child_name: str):
    """
    Get the child of a CswRecord instance

    :param csw_record: the CswRecord instance
    :param child_name: the name of the child to retrieve
    :return: an etree.Element for this child
    """
    root_node = etree.fromstring(csw_record.xml)
    return root_node.find(child_name, namespaces=MUNDI_NAMESPACES)


# For retro compatibility
def findnode(cswRecord: CswRecord, match: str):
    logger.warning(
        'This function will be removed in future versions of mundilib. In order to for you code to run with these '
        'future versions, please consider using "get_node" function instead')
    return get_node(cswRecord, match)


# --------------------------
# RESPONSE WRAPPER
# --------------------------
def _find_entries(response_wrapper: ResponseWrapper):
    """
    Find all atom:entry elements in a ResponseWrapper instance

    :param response_wrapper: the ResponseWrapper instance
    :return: a list of etree.Element whose tags are atom:entry
    """
    root_node = etree.fromstring(response_wrapper.read())
    return root_node.findall('atom:entry', namespaces=MUNDI_NAMESPACES)


def find_entries(response_wrappers: List[ResponseWrapper]):
    """
    Find all atom:entry elements in a list of ResponseWrappers

    :param response_wrappers: the list of ResponseWrappers
    :return: a list of etree.Element whose tags are atom:entry
    """
    entries = []
    for rw in response_wrappers:
        entries += _find_entries(rw)
    return entries


# For retro compatibility
def findentries(ListResponseWrapper):
    logger.warning(
        'This function will be removed in future versions of mundilib. In order to for you code to run with these '
        'future versions, please consider using "find_entries" function instead')
    return find_entries(ListResponseWrapper)


# --------------------------
# OPENSEARCH
# --------------------------
class OpenSearchDescription:
    def __init__(self, opensearch_document_url: str):
        # root node of OS description document
        self.root = etree.fromstring(openURL(opensearch_document_url, method='Get').read())

    def xpath(self, query: str) -> List[etree.Element]:
        return self.root.xpath(query, namespaces=MUNDI_NAMESPACES)

    def find(self, query: str) -> etree.Element:
        return self.root.find(query, namespaces=MUNDI_NAMESPACES)

    def findall(self, query: str) -> List[etree.Element]:
        return self.root.findall(query, namespaces=MUNDI_NAMESPACES)


def opensearch_query(collection, query='', data=None, method='Get', cookies=None, username=None, password=None,
                     timeout=30, headers=None, verify=True, cert=None, params=None):
    """Get a list of ResponseWrappers from a given OpenSearch request"""
    # if params is provided, query is ignored
    if params is not None:
        query = '&'.join(f'{k}={v}' for k, v in params.items())

    # build base request URI
    os_query_base = f'https://{collection.name}.browse.catalog.mundiwebservices.com/opensearch?{query}'

    # loop through all matched records
    response_wrappers = []
    os_query = f'{os_query_base}&startIndex=1'
    while True:
        # get current page
        page = openURL(os_query, data, method, cookies, username, password, timeout, headers, verify, cert)
        response_wrapper = page.read().replace(b'\n', b'')
        response_wrapper_xml = etree.fromstring(response_wrapper)
        response_wrappers.append(page)

        nb_total = int(response_wrapper_xml.find('os:totalResults', namespaces=MUNDI_NAMESPACES).text)
        nb_page = int(response_wrapper_xml.find('os:itemsPerPage', namespaces=MUNDI_NAMESPACES).text)
        start_index = int(response_wrapper_xml.find('os:startIndex', namespaces=MUNDI_NAMESPACES).text)

        next_record = start_index + nb_page
        if next_record > nb_total:
            break

        os_query = f'{os_query_base}&startIndex={next_record}'

    return response_wrappers


def opensearch_nb_results(collection, query="", data=None, method='Get', cookies=None, username=None,
                          password=None, timeout=30, headers=None, verify=True, cert=None, params=None):
    """Get the number of results from an OpenSearch request"""
    # if params is provided, query is ignored
    if params is not None:
        query = '&'.join(f'{k}={v}' for k, v in params.items())

    # build base request URI
    os_query = f'https://{collection.name}.browse.catalog.mundiwebservices.com/opensearch?{query}'

    # only get first page to read number of results
    page = openURL(os_query, data, method, cookies, username, password, timeout, headers, verify, cert)
    response_wrapper = page.read()
    response_wrapper_xml = etree.fromstring(response_wrapper)

    return int(response_wrapper_xml.find('os:totalResults', namespaces=MUNDI_NAMESPACES).text)


# For retro compatibility
def mundiopenURL2(col="", query="", data=None, method='Get', cookies=None, username=None, password=None, timeout=30,
                  headers=None, verify=True, cert=None):
    logger.warning(
        'This function will be removed in future versions of mundilib. In order to for you code to run with these '
        'future versions, please consider using "opensearch_query" function instead')
    return opensearch_query(col, query, data, method, cookies, username, password, timeout, headers, verify, cert)


# --------------------------
# RETRO COMPATIBILITY
# --------------------------
def width(bbox, height):
    logger.warning(
        'This function will be removed in future versions of mundilib. In order to for you code to run with these '
        'future versions, please consider using "utils.height2width" function instead')
    return utils.height2width(bbox, height)


def height(bbox, width):
    logger.warning(
        'This function will be removed in future versions of mundilib. In order to for you code to run with these '
        'future versions, please consider using "utils.width2height" function instead')
    return utils.width2height(bbox, width)


def polygon_bbox_country(country_name):
    logger.warning(
        'This function will be removed in future versions of mundilib. In order to for you code to run with these '
        'future versions, please consider using "utils.country_polygon_bbox" function instead')
    return utils.country_polygon_bbox(country_name)


def display_polygon_country(country_name, a, color):
    logger.warning(
        'This function will be removed in future versions of mundilib. In order to for you code to run with these '
        'future versions, please consider using "utils.display_country_on_world_map" function instead')
    return utils.display_country_on_world_map(country_name, a, color)


def polygon_bbox_city(city_name):
    logger.warning(
        'This function will be removed in future versions of mundilib. In order to for you code to run with these '
        'future versions, please consider using "utils.city_polygon_bbox" function instead')
    return utils.city_polygon_bbox(city_name)


def display_city_wms(polygon, bbox, height, wms_layers, time):
    logger.warning(
        'This function will be removed in future versions of mundilib. In order to for you code to run with these '
        'future versions, please consider using "utils.display_wms" function instead')
    c = MundiCatalogue()
    wms = c.get_collection('Sentinel2').mundi_wms('L1C')
    return utils.display_wms(polygon, bbox, wms, wms_layers, time, height=512)

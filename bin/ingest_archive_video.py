#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Xinru Yan <xinru1414@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Usage:
#   python -v PATH_TO_VIDEO_DIR
#
# Video dir contains a list of videos need to be ingested, for example
#
# videos/
#    N13-1001.mp4
#    N13-1002.mp4
#    ...
#
#

import click
import os, glob
import lxml.etree as et
import argparse
from typing import List, Tuple
from anthology.utils import deconstruct_anthology_id, make_simple_element, indent

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "../data/xml")


def get_collection_ids(video_dir: str) -> List[str]:
    '''
    Go over all the .mp4 files in the video dir and extract unique collection ids, which will be used to identify xmls that need to be updated.

    param:
    video_dir: directory contains video files, eg: /Users/xinruyan/Dropbox/naacl-2013/

    return:
    a list of unique collection ids, eg: ['N13', 'Q13']
    '''
    collection_ids = list(
        set(
            [
                deconstruct_anthology_id(file[len(video_dir) :].split('.')[0])[0]
                for file in glob.glob(f"{video_dir}/*.mp4")
            ]
        )
    )
    return collection_ids


def get_anth_ids(video_dir: str) -> Tuple[List[str], List[List[str]]]:
    '''
    Go over all the .mp4 files in the video dir and extract two types of anthology ids, which will be used to identify papers that needs video tag.

    param:
    video_dir: directory contains video files, eg: /Users/xinruyan/Dropbox/naacl-2013/

    return:
    a tuple, (anth_ids_single, anth_ids_multiple),
    anth_ids_single: a list of anth_ids which only has one video to ingest, eg: ['N13-1118', 'N13-1124']
    anth_ids_multiple: a list of list of [anth_ids], [vid_num] which has multiple videos to ingest, eg: [['N13-4001', '1'],['N13-4001', '2'],['N13-4002', '1'],['N13-4002', '2']. vid_num represents the numbered videos.
    '''
    anth_ids_single = [
        file[len(video_dir) :].split('.')[0]
        for file in glob.glob(f"{video_dir}/*.mp4")
        if len(file[len(video_dir) :].split('.')) == 2
    ]
    anth_ids_multiple = [
        file[len(video_dir) :].split('.')[0:-1]
        for file in glob.glob(f"{video_dir}/*.mp4")
        if len(file[len(video_dir) :].split('.')) > 2
    ]
    anth_ids_multiple.sort()
    return anth_ids_single, anth_ids_multiple


def add_video_tag_single(anth_id, xml_parse):
    '''
    Add video tag for paper f'{anth_id}'
    '''
    collection_id, volume_id, paper_id = deconstruct_anthology_id(anth_id)
    paper = xml_parse.find(f'./volume[@id="{volume_id}"]/paper[@id="{paper_id}"]')
    video_url = anth_id + '.mp4'
    make_simple_element("video", attrib={"href": video_url}, parent=paper)


def add_video_tag_multiple(anth_id, vid_num, xml_parse):
    '''
    Add video tag for paper f`{anth_id}` with multiple number of videos
    Adapted from add_video_tags.py
    '''
    collection_id, volume_id, paper_id = deconstruct_anthology_id(anth_id)
    paper = xml_parse.find(f'./volume[@id="{volume_id}"]/paper[@id="{paper_id}"]')
    video_url = anth_id + f'.{vid_num}' + '.mp4'
    make_simple_element("video", attrib={"href": video_url}, parent=paper)


def update_xml(data_dir, collection_id, extention, xml_tree):
    '''
    Update xml
    Adapted from add_video_tags.py
    '''
    with open(os.path.join(data_dir, collection_id + extention), 'wb') as f:
        indent(xml_tree.getroot())
        xml_tree.write(f, encoding="UTF-8", xml_declaration=True)


@click.command()
@click.option(
    '-v',
    '--video_dir',
    default='/Users/xinruyan/Dropbox/naacl-2013/',
    help='Directory contains all videos need to be ingested',
)
def main(video_dir):
    collection_ids = get_collection_ids(video_dir=video_dir)

    xml_files = [
        file
        for file in os.listdir(DATA_DIR)
        if os.path.splitext(file)[0] in collection_ids
    ]

    anth_ids_single, anth_ids_multiple = get_anth_ids(video_dir=video_dir)

    for file in xml_files:
        collection_id, extention = os.path.splitext(file)
        tree = et.parse(os.path.join(DATA_DIR, file))
        for anth_id in anth_ids_single:
            if collection_id in anth_id:
                add_video_tag_single(anth_id=anth_id, xml_parse=tree)
                update_xml(
                    data_dir=DATA_DIR,
                    collection_id=collection_id,
                    extention=extention,
                    xml_tree=tree,
                )

        for anth_id_vid_num in anth_ids_multiple:
            anth_id = anth_id_vid_num[0]
            vid_num = anth_id_vid_num[1]
            if collection_id in anth_id:
                add_video_tag_multiple(anth_id=anth_id, vid_num=vid_num, xml_parse=tree)
                update_xml(
                    data_dir=DATA_DIR,
                    collection_id=collection_id,
                    extention=extention,
                    xml_tree=tree,
                )


if __name__ == '__main__':
    main()

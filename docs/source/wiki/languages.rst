Supported Languages
===================

The follwing list reflects the languages supported by the BBF for which we additionally tested their correctness:

.. list-table:: 
    :header-rows: 1    
    :widths: 20 20 40 20

    * - Language Name
      - ISO 639-1 Code
      - Pre Processor Source Code
      - Pre Processing Type

    * - English
      - en
      - `Snowball stemmer <https://github.com/snowballstem/snowball>`_
      - Stemmer

    * - Spanish
      - es
      - `Snowball stemmer <https://github.com/snowballstem/snowball>`_
      - Stemmer

    * - French
      - fr
      - `Snowball stemmer <https://github.com/snowballstem/snowball>`_
      - Stemmer

    * - German
      - de
      - `Snowball stemmer <https://github.com/snowballstem/snowball>`_
      - Stemmer

    * - Portuguese
      - pt
      - `Snowball stemmer <https://github.com/snowballstem/snowball>`_
      - Stemmer

    * - Catalan
      - ca
      - `Snowball stemmer <https://github.com/snowballstem/snowball>`_
      - Stemmer

    * - Luxembourgish
      - lb
      - `spellux <https://github.com/questoph/spellux>`_
      - Lemmatizer

Snowball stemmer
----------------

The `snowball stemmer <https://github.com/snowballstem/snowball>`_ supports more languages than the ones displayed in the table above.
For the complete list check out https://snowballstem.org/algorithms/.

Luxembourgish Pre-processing
----------------------------
To support the luxembourgish language, we wanted to enable luxembourgish-specific text-processing. 
For that purpose, we opted for the best available tool, which is the lemmatizer created by Christoph Purschke as part of `"spellux - Automatic text normalization for Luxembourgish" <https://github.com/questoph/spellux>`_.

/// \brief Check that the \p value conforms to its \p value_type.
bool ValueConsistentWithXsdType(
  const std::wstring& value,
  types::DataTypeDefXsd value_type
);

/**
 * \brief Check that \p value is a valid `xs:date`.
 *
 * Year 1 BCE is the last leap BCE year.
 * See: https://www.w3.org/TR/xmlschema-2/#dateTime.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:date`
 */
bool IsXsDate(const std::wstring& text);

/**
 * \brief Check that \p value is a valid `xs:double`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:double`
 */
bool IsXsDouble(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:float`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:float`
 */
bool IsXsFloat(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:gMonthDay`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:gMonthDay`
 */
bool IsXsGMonthDay(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:long`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:long`
 */
bool IsXsLong(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:int`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:int`
 */
bool IsXsInt(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:short`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:short`
 */
bool IsXsShort(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:byte`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:byte`
 */
bool IsXsByte(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:unsignedLong`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:unsignedLong`
 */
bool IsXsUnsignedLong(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:unsignedInt`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:unsignedInt`
 */
bool IsXsUnsignedInt(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:unsignedShort`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:unsignedShort`
 */
bool IsXsUnsignedShort(const std::wstring& value);

/**
 * \brief Check that \p value is a valid `xs:unsignedByte`.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:unsignedByte`
 */
bool IsXsUnsignedByte(const std::wstring& value);
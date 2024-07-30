python3 -c "
with open('pyproject.toml', 'rt') as file:
    pyproject_template= file.read()

with open('pyproject.toml', 'wt') as file:
    file.write(
        pyproject_template.replace(
            '%PACKAGE_VERSION%', '$PACKAGE_VERSION'
        )
    )
"

python3 -m build

import { useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import { useParams } from "react-router-dom"
// import { Remark, useRemark, useRemarkSync } from 'react-remark'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
// import remarkParse from 'remark-parse'
import remarkHighlightjs from 'remark-highlight.js'
// import remarkHtml from 'remark-html'
// import remarkPrettier from 'remark-prettier'
// import prism from 'remark-prism'
import remarkGemoji from 'remark-gemoji'
import authHeader from '../services/auth.header'
import axios from 'axios'
import customUrls from '../services/customUrls'

import { ThemeColors } from '@src/utility/context/ThemeColors'
import { useSkin } from '@hooks/useSkin'
require('@src/assets/scss/markdown.css')

const Documentos = () => {

    const { id } = useParams()

    const [markdown, setMarkdown] = useState("Espera a que cargue el documento...")

    useEffect(async () => {
        const res = await axios({
            method: 'get',
            url: `${customUrls.ApiUrl()}markdown/${id}`,
            headers: authHeader()
        })
        console.log("Markdown:")
        console.log(res.data)
        setMarkdown(res.data)
    }, [id])
  
    // const contenido = useRemarkSync(markdown, {remarkPlugins: [remarkHighlightjs, remarkParse,  remarkGemoji]})

    return (
        <Card>
            <CardBody>
            <ReactMarkdown children={markdown} remarkPlugins={[remarkGemoji, remarkHighlightjs, remarkGfm]} />
            </CardBody>
        </Card>
    )

}
export default Documentos